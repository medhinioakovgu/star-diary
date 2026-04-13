import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity } from 'react-native';
import { theme } from '../theme';

interface DiaryPageProps {
  question: string;
  onSubmit: (text: string) => void;
}

export const DiaryPage: React.FC<DiaryPageProps> = ({ question, onSubmit }) => {
  const [inputText, setInputText] = useState('');

  const currentDate = new Date();
  const dateString = currentDate.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
  }).toUpperCase();

  const handleSubmit = () => {
    if (inputText.trim()) {
      onSubmit(inputText.trim());
      setInputText('');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.date}>{dateString}</Text>
      </View>

      <View style={styles.questionContainer}>
        <Text style={styles.question}>"{question}"</Text>
      </View>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.diaryInput}
          placeholder="Write your thoughts here..."
          placeholderTextColor={theme.colors.deepBlack + '80'} // semi-transparent
          value={inputText}
          onChangeText={setInputText}
          multiline
          autoFocus
          onSubmitEditing={handleSubmit}
        />
      </View>

      {inputText.trim() && (
        <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
          <Text style={styles.submitButtonText}>Submit Entry</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.cloudDancer,
    paddingHorizontal: 20,
    paddingTop: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  date: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.deepBlack,
    letterSpacing: 2,
    fontFamily: 'System', // sans-serif
  },
  questionContainer: {
    marginBottom: 40,
    paddingHorizontal: 10,
  },
  question: {
    fontSize: 28,
    fontStyle: 'italic',
    color: theme.colors.deepBlack,
    fontFamily: 'PlayfairDisplay-Regular',
    textAlign: 'center',
    lineHeight: 36,
  },
  inputContainer: {
    flex: 1,
    marginBottom: 20,
  },
  diaryInput: {
    flex: 1,
    fontSize: 18,
    color: theme.colors.deepBlack,
    fontFamily: 'CedarvilleCursive-Regular',
    backgroundColor: 'transparent',
    borderWidth: 0,
    padding: 0,
    textAlignVertical: 'top',
    lineHeight: 28,
  },
  submitButton: {
    backgroundColor: theme.colors.gold,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
    alignSelf: 'center',
    marginBottom: 20,
  },
  submitButtonText: {
    color: theme.colors.deepBlack,
    fontSize: 16,
    fontFamily: 'PlayfairDisplay-Regular',
    fontWeight: '600',
  },
});