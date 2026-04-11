
import React, { useState, useRef } from 'react';
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
import { theme } from './theme';
import { DiaryCover } from './components/DiaryCover';
import { DiaryPage } from './components/DiaryPage';

// --- TYPES ---
type Message = {
  id: string;
  text: string;
  sender: 'user' | 'paparazzo';
};

const { width } = Dimensions.get('window');

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
  const flatListRef = useRef<FlatList>(null);

  // --- NETWORKING ---
  // ⚠️ CRUCIAL: Change this depending on how you test!
  // iOS Simulator: 'http://localhost:8000/api/chat'
  // Android Emulator: 'http://10.0.2.2:8000/api/chat'
  // Physical Device: 'http://<YOUR_LAPTOP_WIFI_IP>:8000/api/chat'
  const BACKEND_URL = 'http://10.0.2.2:8000/api/chat';

  const sendMessage = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText) return;

    const newUserMsg: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      // Send to FastAPI Backend
      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newUserMsg.text }), // Ensure this matches your FastAPI Pydantic model
      });

      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      
      const newAiMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: data.reply || "No comment? Come on, give me something!", // Fallback text
        sender: 'paparazzo',
      };

      setMessages((prev) => [...prev, newAiMsg]);
    } catch (error) {
      console.error("Failed to fetch from backend:", error);
      // Optional: Add a system message here saying "Connection failed"
    } finally {
      setIsLoading(false);
      setShowChat(true);
    }
  };

  const rotateY = flipAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '-110deg'],
  });

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
    return (
      <View style={[styles.messageRow, isUser ? styles.messageRowUser : styles.messageRowAi]}>
        <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>
          {item.text}
        </Text>
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
                  <Text style={styles.headerTitle}>📸 Star Diary</Text>
                </View>

                {/* Chat Area */}
                <KeyboardAvoidingView 
                  style={styles.keyboardAvoidingView} 
                  behavior={Platform.OS === 'ios' ? 'padding' : undefined}
                >
                  <FlatList
                    ref={flatListRef}
                    data={messages}
                    keyExtractor={(item) => item.id}
                    renderItem={renderMessage}
                    contentContainerStyle={styles.flatListContent}
                    onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
                  />

                  {isLoading && (
                    <View style={styles.loadingContainer}>
                      <ActivityIndicator size="small" color={theme.colors.spineGold} />
                      <Text style={styles.loadingText}>Paparazzo is typing...</Text>
                    </View>
                  )}

                  {/* Input Area */}
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
                </KeyboardAvoidingView>
              </>
            ) : (
              <DiaryPage
                question={messages[0]?.text || "What's on your mind today?"}
                onSubmit={(text) => sendMessage(text)}
              />
            )}
          </Animated.View>
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
  animatedView: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  coverAnimatedView: {
    transform: [{ perspective: 1000 }],
  },
  header: {
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.spineGold,
    alignItems: 'center',
    backgroundColor: theme.colors.deepBlack,
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
});