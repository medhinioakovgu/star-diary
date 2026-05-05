import React, { useState, useRef, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Dimensions,
  Animated,
  Easing,
  Keyboard,
  Alert,
} from 'react-native';
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFonts } from 'expo-font';
import {
  PlayfairDisplay_400Regular,
} from '@expo-google-fonts/playfair-display';
import {
  CedarvilleCursive_400Regular,
} from '@expo-google-fonts/cedarville-cursive';
import { LinearGradient } from 'expo-linear-gradient';
import OpenAI from 'openai';
import { theme } from './theme';
import { DiaryCover } from './components/DiaryCover';
import { DiaryPage } from './components/DiaryPage';
import {
  getMessagesForDate,
  setMessagesForDate,
  getWeekStartDate,
  setWeekStartDate,
  getLastSessionDate,
  setLastSessionDate,
  todayIso,
  dayNumberFor,
  clearAll
} from './storage';

// --- TYPES ---
type Message = {
  id: string;
  text: string;
  sender: 'user' | 'paparazzo';
};

const { width } = Dimensions.get('window');

// --- OPENAI CLIENT ---
// dangerouslyAllowBrowser: true is required for the SDK to run in React Native / Expo
const openai = new OpenAI({
  apiKey: process.env.EXPO_PUBLIC_OPENAI_API_KEY,
  dangerouslyAllowBrowser: true,
});

// --- PAPARAZZO SYSTEM PROMPT (verbatim from research/prompts.py — do not edit) ---
const PAPARAZZO_INTERVIEWER_PROMPT = `You are 'Snap', a relentless, dramatic, and slightly invasive celebrity paparazzi reporter for a high-end gossip magazine. You are interviewing the user, who is a massively famous A-list celebrity giving an exclusive daily statement to the press.

YOUR GOAL:
Extract concrete details about the user's day -- what they did, who they saw, what they ate, where they went, how they felt -- and frame every question as if you are chasing the next tabloid headline.

RULES:
1. NEVER break character. NEVER say "As an AI" or "I'm here to help."
2. Keep every response SHORT and PUNCHY -- 1 to 3 sentences maximum. This is a fast-paced doorstep interview, not a conversation.
3. Use dramatic tabloid lingo: "Spotted!", "Exclusive!", "Sources say...", "Word on the street...", "The tea is piping hot..."
4. Always end with a probing, slightly nosy follow-up question about something specific they just mentioned. Push for names, places, times, feelings.
5. React to what they said before asking the next question -- make them feel heard and watched.
6. If their day sounds ordinary, stay curious rather than inventing drama. A great reporter finds the story IN the truth, not on top of it. Ask sharper questions, don't manufacture scandal.
7. Aim to cover 6-8 probing questions across the full interview. Vary the angles: people, places, emotions, decisions, small details.

TONE: Breathless, fascinated, a little nosy, never mean.`;

function formatMessageTime(messageId: string): string | null {
  // The greeting message has id='1' — no timestamp to show
  if (messageId === '1') return null;

  const ms = parseInt(messageId, 10);
  if (Number.isNaN(ms) || ms < 1_000_000_000_000) return null; // sanity check

  const d = new Date(ms);
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

function stripTrailingQuestion(text: string): string {
  // Split into sentences (rough heuristic — works for English well enough)
  const sentences = text.split(/(?<=[.!?])\s+/);
  // Walk backwards, drop trailing sentences that end in '?'
  while (sentences.length > 1 && sentences[sentences.length - 1].trim().endsWith('?')) {
    sentences.pop();
  }
  let result = sentences.join(' ').trim();
  // If we stripped everything, fall back to a default closing
  if (result.length === 0 || sentences.length === 0) {
    result = "That's a wrap, superstar. See you tomorrow!";
  }
  return result;
}

// --- DAY-COMPLETE CELEBRATION PANEL ---
function DayCompletePanel({
  activeDate,
  weekStartIso,
  onDismiss,
}: {
  activeDate: string;
  weekStartIso: string;
  onDismiss: () => void;
}) {
  const dayNum = dayNumberFor(activeDate, weekStartIso);
  const dateStr = new Date(activeDate + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  return (
    <TouchableOpacity
      style={styles.dayCompleteContainer}
      onPress={onDismiss}
      activeOpacity={0.8}
    >
      <Text style={styles.dayCompleteSparkles}>✨</Text>
      <Text style={styles.dayCompleteTitle}>Day {dayNum} of 7 — captured</Text>
      <Text style={styles.dayCompleteDate}>{dateStr}</Text>
      <Text style={styles.dayCompleteHint}>Tap to continue</Text>
    </TouchableOpacity>
  );
}

// --- COUNTDOWN PANEL ---
function CountdownPanel() {
  const [tick, setTick] = useState(0);

  useEffect(() => {
    // Re-render every minute to refresh the countdown
    const interval = setInterval(() => setTick((t) => t + 1), 60_000);
    return () => clearInterval(interval);
  }, []);

  const msUntilMidnight = (() => {
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0); // start of next day
    return midnight.getTime() - now.getTime();
  })();

  const totalMinutes = Math.max(0, Math.floor(msUntilMidnight / 60_000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  let countdownText: string;
  if (totalMinutes <= 1) {
    countdownText = 'Any minute now, superstar.';
  } else if (totalMinutes < 60) {
    countdownText = `${totalMinutes} minutes until your next exclusive.`;
  } else if (hours < 2) {
    countdownText = `1 hour ${minutes} minutes until your next exclusive.`;
  } else {
    countdownText = `${hours} hours until your next exclusive.`;
  }

  return (
    <View style={styles.sessionEndedContainer}>
      <Text style={styles.sessionEndedText}>That's today's exclusive! ✨</Text>
      <Text style={styles.sessionEndedSubtext}>{countdownText}</Text>
    </View>
  );
}

// --- DATE BAR (sticky, below main header) ---
function DateBar({
  activeDate,
  weekStartIso,
}: {
  activeDate: string;
  weekStartIso: string;
}) {
  const dayNum = dayNumberFor(activeDate, weekStartIso);
  // Format as "5 May" — day-month, short month name
  const d = new Date(activeDate + 'T00:00:00');
  const day = d.getDate();
  const month = d.toLocaleDateString('en-US', { month: 'long' });

  return (
    <View style={styles.dateBar}>
      <Text style={styles.dateBarText}>
        Day {dayNum} of 7  ·  {day} {month}
      </Text>
    </View>
  );
}

// --- LINED PAPER BACKGROUND ---
function LinedPaperBackground() {
  const lines = [];
  const lineSpacing = 32; // pixels between lines — tune to match font size
  const numLines = 50; // enough to fill any reasonable scroll length
  for (let i = 0; i < numLines; i++) {
    lines.push(
      <View
        key={i}
        style={[
          styles.paperLine,
          { top: i * lineSpacing },
        ]}
      />
    );
  }
  return <View style={styles.paperLinesContainer} pointerEvents="none">{lines}</View>;
}

export default function App() {
  const [fontsLoaded] = useFonts({
    'PlayfairDisplay-Regular': PlayfairDisplay_400Regular,
    'CedarvilleCursive-Regular': CedarvilleCursive_400Regular,
  });

  const coverAnim = useRef(new Animated.Value(0)).current;
  const diaryAnim = useRef(new Animated.Value(width)).current;
  const flipAnim = useRef(new Animated.Value(0)).current;
  const [isOpen, setIsOpen] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const [messages, setMessages] = useState<Message[]>([
  { id: '1', text: 'Hey superstar! Ready to spill the tea on your day?', sender: 'paparazzo' }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeDate, setActiveDate] = useState<string>(todayIso()); // ISO date the current session belongs to
  const [weekStartDate, setWeekStartDateState] = useState<string>(todayIso());
  const [questionCount, setQuestionCount] = useState(0); // Paparazzo replies sent today (excluding the greeting)

  const [resetKey, setResetKey] = useState(0);
  // Total Paparazzo replies in a day: 8 question-asking turns + 1 closing remark = 9.
  const TOTAL_REPLIES = 9;
  const sessionEnded = questionCount >= TOTAL_REPLIES;

  const [showDayComplete, setShowDayComplete] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  // --- LOAD PERSISTED MESSAGES ON MOUNT ---
  // If there's prior chat from today, skip the cover animation and jump straight in
  useEffect(() => {
  (async () => {
    const today = todayIso();

    // First-ever launch? Set the week's start date.
    let weekStart = await getWeekStartDate();
    if (!weekStart) {
      await setWeekStartDate(today);
      weekStart = today;
    }
    setWeekStartDateState(weekStart);
    // Determine which date the active session belongs to.
    const last = await getLastSessionDate();
    let sessionDate = today;
    // If there was a previous session and it was today, continue it.
    // If it was a different day, that day is archived; we start fresh today.
    if (last && last !== today) {
      // last session is from a previous date — leave its messages in storage
      // (they're queryable later via listJournaledDates()) and start a fresh day.
      sessionDate = today;
    }
    setActiveDate(sessionDate);
    await setLastSessionDate(sessionDate);

    // Load any messages already journaled today.
    const stored = await getMessagesForDate(sessionDate);
    if (stored.length > 0) {
      setMessages(stored);
      // Count Paparazzo replies, excluding the hardcoded greeting (id === '1')
      const replies = stored.filter((m) => m.sender === 'paparazzo' && m.id !== '1').length;
      setQuestionCount(replies);
      setShowChat(true);
    }
  })();
}, []);

    const sendMessage = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText) return;
    if (sessionEnded) return; // Hard stop, should not be reachable

    if (!showChat) setShowChat(true);
    setIsLoading(true);

    const newUserMsg: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
    };

    setMessages((prev) => {
      const updated = [...prev, newUserMsg];
      setMessagesForDate(activeDate, updated);
      return updated;
    });
    setInputText('');

    try {
      const chatHistory = messages.map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text,
      })) as { role: 'user' | 'assistant' | 'system'; content: string }[];

      // Routing logic — what kind of reply should the LLM produce?
      // questionCount = number of Paparazzo replies already sent (excluding greeting).
      // The LLM's NEXT reply is reply number (questionCount + 1).
      const nextReplyNum = questionCount + 1;

      let routingInstruction: string;
      if (nextReplyNum === 1) {
        // First real reply — set the day's coverage frame
        routingInstruction = `This is reply 1 of 9 in today's interview. You have exactly 8 question-asking turns to cover this person's day, then 1 closing remark.

  To capture the full day, make sure you've explored ALL of these angles before your 8th question: people they saw, places they went, events that happened, feelings/emotions, decisions they made, and at least one memorable direct quote. Don't get stuck on one topic. If they linger on something for 2 turns in a row, redirect them: "You've spilled enough about [topic] — what about [uncovered angle]?" That's the Paparazzo voice. Be a little nosy, redirect with charm.

  Now react to what they said and ask your first question.`;
      } else if (nextReplyNum >= 2 && nextReplyNum <= 5) {
        routingInstruction = `This is question ${nextReplyNum} of 8 in today's interview. Continue naturally. Remember to vary angles (people, places, events, feelings, decisions, quotes). If they've been on one topic too long, redirect: "Enough about [topic], darling — what about [uncovered angle]?"`;
      } else if (nextReplyNum === 6) {
        routingInstruction = `This is question 6 of 8 in today's interview. You have only 2 questions remaining after this.

        REQUIRED FORMAT for this reply:
        1. First sentence: a tabloid-style time-pressure warning. Pick one: "We're running out of column inches, superstar — the editor needs the headline by midnight!" or "Three more lines until deadline, darling — what's the real story here?" or invent one in this voice.
        2. Then ask one probing question targeting whichever angle (people / places / events / feelings / decisions / direct quotes) is least covered so far.

        Do not skip the warning sentence. It anchors the user emotionally for the wrap-up.`;
        } else if (nextReplyNum === 7) {
        routingInstruction = `This is question 7 of 8 in today's interview. One more question after this. Make it count. Target whichever angle (people / places / events / feelings / decisions / quotes) is still least covered.`;
      } else if (nextReplyNum === 8) {
        routingInstruction = `This is question 8 of 8 — your FINAL question for today's interview. Ask one closing question that captures the most important still-uncovered angle of their day. Make it probing and specific.`;
      } else {
        // nextReplyNum === 9 — closing remark, NO question
        routingInstruction = `OVERRIDE: The user has now answered all 8 questions. Today's interview is OVER. The "always end with a question" rule from your earlier instructions DOES NOT APPLY to this reply.

      REQUIRED FORMAT:
      1. One sentence reacting warmly to what they just said.
      2. One sentence sign-off in Paparazzo voice.

      Examples of valid sign-offs:
      - "That's a wrap, superstar — see you tomorrow!"
      - "And cut! Get some rest, darling — tomorrow's edition awaits."
      - "The presses are rolling — sleep tight, my favorite headline."

      DO NOT ASK A QUESTION. Maximum 2 sentences total. Your reply MUST end with one of the sign-off styles above (or similar).`;
      }

      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        temperature: 0.7,
        max_tokens: 512,
        messages: [
          { role: 'system', content: PAPARAZZO_INTERVIEWER_PROMPT },
          { role: 'system', content: routingInstruction },
          ...chatHistory,
          { role: 'user', content: messageText },
        ],
      });

      const replyText = response.choices[0].message.content || "No comment? Come on, give me something!";

      const newAiMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: replyText,
        sender: 'paparazzo',
      };

      setMessages((prev) => {
        const updated = [...prev, newAiMsg];
        setMessagesForDate(activeDate, updated);
        return updated;
      });
      setQuestionCount((n) => n + 1);

      // If this was the closing remark (reply 9), show the celebration
      let finalReplyText = replyText;
      if (nextReplyNum === 9) {
        finalReplyText = stripTrailingQuestion(replyText);
        setShowDayComplete(true);
      }
    } catch (error) {
      console.error("Failed to call OpenAI:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const rotateY = flipAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '-110deg'],
  });

  const performReset = async () => {
  await clearAll();
  setMessages([{ id: '1', text: 'Hey superstar! Ready to spill the tea on your day?', sender: 'paparazzo' }]);
  setQuestionCount(0);
  setShowDayComplete(false);
  setShowChat(false);
  setIsOpen(false);
  setActiveDate(todayIso());
  setWeekStartDateState(todayIso());

  // Reset the cover animation state — without this, the diary stays "open" visually
  coverAnim.setValue(0);
  diaryAnim.setValue(width);
  flipAnim.setValue(0);
  setResetKey((k) => k + 1);
};

const handleRefreshPress = () => {
  // TODO: remove before demo — this is a testing-only reset
  Alert.alert(
    "Reset today's session?",
    "This clears today's chat and starts a fresh interview. (Dev/testing only.)",
    [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Reset', style: 'destructive', onPress: performReset },
    ]
  );
};

  const handleBeginJournal = () => {
    setIsOpen(true);

    Animated.parallel([
      Animated.timing(coverAnim, {
        toValue: -width,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(diaryAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(flipAnim, {
        toValue: 1,
        duration: 800,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start();
  };

  // --- UI RENDERERS ---
  const renderMessage = ({ item }: { item: Message }) => {
  const isUser = item.sender === 'user';
  const time = formatMessageTime(item.id);
  return (
    <View style={[styles.messageRow, isUser ? styles.messageRowUser : styles.messageRowAi]}>
      <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>
        {item.text}
      </Text>
      {time && (
        <Text style={[styles.messageTime, isUser ? styles.messageTimeUser : styles.messageTimeAi]}>
          {time}
        </Text>
      )}
    </View>
  );
};

  if (!fontsLoaded) {
    return null;
  }

  return (
    <LinearGradient
      colors={[theme.colors.cloudDancer, theme.colors.silkyEnd]}
      start={{ x: 0, y: 0 }} // top-left
      end={{ x: 1, y: 1 }} // bottom-right
      style={styles.gradient}
    >
      <SafeAreaProvider>
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
          <View key={resetKey} style={{ flex: 1 }}>
          <Animated.View style={[styles.animatedView, styles.coverAnimatedView, {
            transform: [
              { perspective: 1000 },
              { translateX: width / 2 },
              { rotateY: isOpen ? rotateY : '0deg' },
              { translateX: -width / 2 },
              { translateX: coverAnim },
            ],
          }]}>
            <DiaryCover onOpen={handleBeginJournal} />
          </Animated.View>
          <Animated.View style={[styles.animatedView, { transform: [{ translateX: diaryAnim }] }]}>
            {showChat ? (
              <>
                {/* Header */}
                <View style={styles.header}>
                  <View style={styles.headerSpacer} />
                  <Text style={styles.headerTitle}>📸 Star Diary</Text>
                  <TouchableOpacity onPress={handleRefreshPress} style={styles.refreshButton}>
                    <Ionicons name="refresh" size={20} color={theme.colors.spineGold} />
                  </TouchableOpacity>
                </View>

                {/* Date bar */}
                <DateBar activeDate={activeDate} weekStartIso={weekStartDate} />

                {/* Chat Area */}
                <KeyboardAvoidingView
                  style={styles.keyboardAvoidingView}
                  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                  keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
                >
                  <View style={{ flex: 1 }}>
                  <LinedPaperBackground />
                  <FlatList
                    ref={flatListRef}
                    data={messages}
                    keyExtractor={(item) => item.id}
                    renderItem={renderMessage}
                    contentContainerStyle={styles.flatListContent}
                    onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
                    keyboardShouldPersistTaps="handled"
                    onScrollBeginDrag={Keyboard.dismiss}
                  />
                  </View>


                  {isLoading && (
                    <View style={styles.loadingContainer}>
                      <ActivityIndicator size="small" color={theme.colors.spineGold} />
                      <Text style={styles.loadingText}>Paparazzo is typing...</Text>
                    </View>
                  )}

                  {/* Input Area */}
                  {sessionEnded ? (
                    showDayComplete ? (
                      <DayCompletePanel
                        activeDate={activeDate}
                        weekStartIso={weekStartDate}
                        onDismiss={() => setShowDayComplete(false)}
                      />
                    ) : (
                      <CountdownPanel />
                    )
                  ) : (
                    <View style={styles.inputContainer}>
                      <TextInput
                        style={styles.textInput}
                        placeholder="Tell your story..."
                        placeholderTextColor="#999"
                        value={inputText}
                        onChangeText={setInputText}
                        multiline
                      />
                      <TouchableOpacity
                        style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
                        onPress={() => sendMessage()}
                        disabled={!inputText.trim() || isLoading}
                      >
                        <Ionicons name="send" size={20} color="#fff" />
                      </TouchableOpacity>
                    </View>
                  )}
                </KeyboardAvoidingView>
              </>
            ) : (
              <DiaryPage
                question={messages[0]?.text || "What's on your mind today?"}
                onSubmit={(text) => sendMessage(text)}
              />
            )}
          </Animated.View>
          </View>
        </SafeAreaView>
      </SafeAreaProvider>
    </LinearGradient>
  );
}

// --- STYLES ---
const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent', // Let gradient show through
  },
    sessionEndedContainer: {
    padding: 24,
    backgroundColor: theme.colors.deepBlack,
    borderTopWidth: 1,
    borderTopColor: theme.colors.spineGold,
    alignItems: 'center',
  },
  sessionEndedText: {
    color: theme.colors.spineGold,
    fontSize: 18,
    fontFamily: 'PlayfairDisplay-Regular',
    fontWeight: 'bold',
    marginBottom: 4,
  },
  sessionEndedSubtext: {
    color: '#999',
    fontSize: 14,
    fontStyle: 'italic',
  },
  animatedView: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  dayCompleteContainer: {
  padding: 32,
  backgroundColor: theme.colors.deepBlack,
  borderTopWidth: 1,
  borderTopColor: theme.colors.spineGold,
  alignItems: 'center',
  },
  dayCompleteSparkles: {
    fontSize: 28,
    marginBottom: 8,
  },
  dayCompleteTitle: {
    color: theme.colors.spineGold,
    fontSize: 20,
    fontFamily: 'PlayfairDisplay-Regular',
    fontWeight: 'bold',
    marginBottom: 4,
    textAlign: 'center',
  },
  dayCompleteDate: {
    color: '#fff',
    fontSize: 14,
    fontFamily: 'PlayfairDisplay-Regular',
    marginBottom: 16,
    textAlign: 'center',
  },
  dayCompleteHint: {
    color: '#999',
    fontSize: 12,
    fontStyle: 'italic',
  },
  coverAnimatedView: {
    transform: [{ perspective: 1000 }],
  },
  header: {
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'space-between',
  paddingVertical: 15,
  paddingHorizontal: 16,
  borderBottomWidth: 1,
  borderBottomColor: theme.colors.spineGold,
  backgroundColor: theme.colors.deepBlack,
},
headerSpacer: {
  width: 36, // matches the refresh button's tap target so title stays centered
},
  headerTitle: {
    ...theme.textStyles.magazineHeader,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  flatListContent: {
    padding: 15,
    paddingBottom: 20,
  },
  messageRow: {
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  messageRowUser: {
    alignItems: 'flex-end',
  },
  messageRowAi: {
    alignItems: 'flex-start',
  },
  messageText: {
    fontSize: 18,
    lineHeight: 26,
    maxWidth: '80%',
  },
  userText: {
    color: '#2E86AB', // Blue ink color
    fontFamily: 'CedarvilleCursive-Regular',
    textAlign: 'right',
  },
  aiText: {
    color: theme.colors.deepBlack,
    fontFamily: 'PlayfairDisplay-Regular',
    fontWeight: 'bold',
    textAlign: 'left',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 10,
  },
  loadingText: {
    marginLeft: 10,
    color: theme.colors.gold,
    fontSize: 14,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    paddingBottom: Platform.OS === 'ios' ? 10 : 20,
    backgroundColor: theme.colors.deepBlack,
    borderTopWidth: 1,
    borderTopColor: theme.colors.spineGold,
    alignItems: 'flex-end',
  },
  textInput: {
  flex: 1,
  minHeight: 40,
  maxHeight: 120,
  backgroundColor: theme.colors.deepBlack,
  borderRadius: 20,
  paddingHorizontal: 15,
  paddingTop: 12,
  paddingBottom: 12,
  ...theme.textStyles.diaryInput,
  color: theme.colors.cloudDancer, // override the dark color from diaryInput; we want light text on dark input
},
  sendButton: {
    marginLeft: 10,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: theme.colors.spineGold,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 2,
  },
  sendButtonDisabled: {
    backgroundColor: '#A0A0A0',
  },
refreshButton: {
  width: 36,
  height: 36,
  alignItems: 'center',
  justifyContent: 'center',
},
dateBar: {
  paddingVertical: 8,
  alignItems: 'center',
  backgroundColor: theme.colors.cloudDancer,
  borderBottomWidth: 1,
  borderBottomColor: 'rgba(212, 175, 55, 0.3)', // spineGold at 30% opacity
},
dateBarText: {
  color: theme.colors.deepBlack,
  fontSize: 13,
  fontFamily: 'PlayfairDisplay-Regular',
  letterSpacing: 0.5,
},
messageTime: {
  fontSize: 10,
  color: '#999',
  marginTop: 2,
  fontFamily: 'PlayfairDisplay-Regular',
},
messageTimeUser: {
  textAlign: 'right',
  alignSelf: 'flex-end',
},
messageTimeAi: {
  textAlign: 'left',
  alignSelf: 'flex-start',
},
paperLinesContainer: {
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
},
paperLine: {
  position: 'absolute',
  left: 0,
  right: 0,
  height: 1,
  backgroundColor: 'rgba(0, 0, 0, 0.06)', // subtle gray, just visible
},
});