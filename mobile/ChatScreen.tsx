/**
 * ChatScreen.tsx – React Native chat UI for The Star-Interview Diary.
 *
 * Displays a conversation between the user and "Paparazzo" (the AI coach).
 * Messages are sent to the FastAPI /chat endpoint and responses are appended
 * to the local chat state.
 */

import React, { useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  ListRenderItemInfo,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

// ---------------------------------------------------------------------------
// API configuration
// Android emulators route "localhost" back to the emulator itself, so we use
// the special alias 10.0.2.2 to reach the host machine.
// ---------------------------------------------------------------------------
const API_BASE =
  Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
const CHAT_URL = `${API_BASE}/chat`;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type Role = 'user' | 'paparazzo';

interface Message {
  id: string;
  role: Role;
  content: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList<Message>>(null);

  // -------------------------------------------------------------------------
  // sendMessage – POST the user's text to the FastAPI backend and append the
  // Paparazzo reply (or an error notice) to the chat state.
  // -------------------------------------------------------------------------
  const sendMessage = async () => {
    const trimmed = inputText.trim();
    if (!trimmed || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmed,
    };

    // Optimistically add the user message and clear the input.
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInputText('');
    setIsLoading(true);

    try {
      // Build the history payload expected by the backend:
      // all previous messages with 'paparazzo' mapped back to 'assistant'.
      const history = nextMessages.slice(0, -1).map((m) => ({
        role: m.role === 'paparazzo' ? 'assistant' : m.role,
        content: m.content,
      }));

      const response = await fetch(CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history, message: trimmed }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const data: { reply: string } = await response.json();

      const paparazzoMsg: Message = {
        id: `${Date.now()}-paparazzo`,
        role: 'paparazzo',
        content: data.reply ?? '(no reply)',
      };

      setMessages((prev) => [...prev, paparazzoMsg]);
    } catch (err) {
      const errorMsg: Message = {
        id: `${Date.now()}-error`,
        role: 'paparazzo',
        content:
          `⚠️ Could not reach the backend. Make sure the FastAPI server is ` +
          `running on port 8000.\n\n(${String(err)})`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // renderItem – render a single chat bubble
  // -------------------------------------------------------------------------
  const renderItem = ({ item }: ListRenderItemInfo<Message>) => {
    const isUser = item.role === 'user';
    return (
      <View
        style={[
          styles.bubbleWrapper,
          isUser ? styles.userWrapper : styles.paparazzoWrapper,
        ]}
      >
        {!isUser && <Text style={styles.roleLabel}>Paparazzo</Text>}
        <View
          style={[
            styles.bubble,
            isUser ? styles.userBubble : styles.paparazzoBubble,
          ]}
        >
          <Text
            style={[
              styles.bubbleText,
              isUser ? styles.userText : styles.paparazzoText,
            ]}
          >
            {item.content}
          </Text>
        </View>
      </View>
    );
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      <FlatList<Message>
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        onContentSizeChange={() =>
          flatListRef.current?.scrollToEnd({ animated: true })
        }
        onLayout={() =>
          flatListRef.current?.scrollToEnd({ animated: true })
        }
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            Start the conversation – ask Paparazzo anything about your interview
            preparation! ⭐
          </Text>
        }
      />

      {isLoading && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color="#6B21A8" />
          <Text style={styles.loadingText}>Paparazzo is thinking…</Text>
        </View>
      )}

      {/* Input bar pinned to the bottom */}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type your message…"
          placeholderTextColor="#9CA3AF"
          multiline
          returnKeyType="default"
          editable={!isLoading}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
          ]}
          onPress={sendMessage}
          disabled={!inputText.trim() || isLoading}
          accessibilityLabel="Send message"
          accessibilityRole="button"
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  listContent: {
    padding: 16,
    paddingBottom: 8,
    flexGrow: 1,
  },
  emptyText: {
    textAlign: 'center',
    color: '#9CA3AF',
    fontSize: 14,
    marginTop: 40,
    paddingHorizontal: 32,
    lineHeight: 22,
  },
  bubbleWrapper: {
    marginVertical: 4,
    maxWidth: '80%',
  },
  userWrapper: {
    alignSelf: 'flex-end',
    alignItems: 'flex-end',
  },
  paparazzoWrapper: {
    alignSelf: 'flex-start',
    alignItems: 'flex-start',
  },
  roleLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 2,
    marginLeft: 4,
  },
  bubble: {
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: '#6B21A8',
    borderBottomRightRadius: 4,
  },
  paparazzoBubble: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderBottomLeftRadius: 4,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: '#FFFFFF',
  },
  paparazzoText: {
    color: '#111827',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 8,
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    backgroundColor: '#FFFFFF',
  },
  textInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    fontSize: 15,
    color: '#111827',
    backgroundColor: '#F9FAFB',
  },
  sendButton: {
    backgroundColor: '#6B21A8',
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 10,
    justifyContent: 'center',
    alignItems: 'center',
    height: 40,
  },
  sendButtonDisabled: {
    backgroundColor: '#D1D5DB',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 15,
  },
});
