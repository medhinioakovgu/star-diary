
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
} from 'react-native';
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

// --- TYPES ---
type Message = {
  id: string;
  text: string;
  sender: 'user' | 'paparazzo';
};

export default function App() {
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

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const newUserMsg: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
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
    }
  };

  // --- UI RENDERERS ---
  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.sender === 'user';
    return (
      <View style={[styles.messageRow, isUser ? styles.messageRowUser : styles.messageRowAi]}>
        <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
          <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>
            {item.text}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
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
              <ActivityIndicator size="small" color="#E1306C" />
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
              onPress={sendMessage}
              disabled={!inputText.trim() || isLoading}
            >
              <Ionicons name="send" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

// --- STYLES ---
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F7F8',
  },
  header: {
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#EAEAEA',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  flatListContent: {
    padding: 15,
    paddingBottom: 20,
  },
  messageRow: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  messageRowUser: {
    justifyContent: 'flex-end',
  },
  messageRowAi: {
    justifyContent: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    padding: 14,
    borderRadius: 20,
  },
  userBubble: {
    backgroundColor: '#007AFF', // iOS Blue
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: '#FFFFFF',
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#FFFFFF',
  },
  aiText: {
    color: '#333333',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 10,
  },
  loadingText: {
    marginLeft: 10,
    color: '#E1306C',
    fontSize: 14,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    paddingBottom: Platform.OS === 'ios' ? 10 : 20,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#EAEAEA',
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    backgroundColor: '#F0F0F0',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingTop: 12,
    paddingBottom: 12,
    fontSize: 16,
    color: '#333',
  },
  sendButton: {
    marginLeft: 10,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#E1306C', // Instagram-ish pink/red for the Paparazzo vibe
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 2,
  },
  sendButtonDisabled: {
    backgroundColor: '#A0A0A0',
  },
});