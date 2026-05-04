import AsyncStorage from '@react-native-async-storage/async-storage';

export type Message = {
  id: string;
  text: string;
  sender: 'user' | 'paparazzo';
};

const KEY_CURRENT_DAY = 'diary:current_day';
const KEY_TRANSCRIPTS = 'diary:transcripts';
const KEY_MESSAGES_TODAY = 'diary:messages_today';

export async function getCurrentDay(): Promise<number> {
  const v = await AsyncStorage.getItem(KEY_CURRENT_DAY);
  return v ? parseInt(v, 10) : 1;
}

export async function setCurrentDay(day: number): Promise<void> {
  await AsyncStorage.setItem(KEY_CURRENT_DAY, day.toString());
}

export async function getMessagesToday(): Promise<Message[]> {
  const v = await AsyncStorage.getItem(KEY_MESSAGES_TODAY);
  return v ? JSON.parse(v) : [];
}

export async function setMessagesToday(messages: Message[]): Promise<void> {
  await AsyncStorage.setItem(KEY_MESSAGES_TODAY, JSON.stringify(messages));
}

export async function getTranscripts(): Promise<Record<string, string>> {
  const v = await AsyncStorage.getItem(KEY_TRANSCRIPTS);
  return v ? JSON.parse(v) : {};
}

export async function setTranscripts(transcripts: Record<string, string>): Promise<void> {
  await AsyncStorage.setItem(KEY_TRANSCRIPTS, JSON.stringify(transcripts));
}

// For demo reset
export async function clearAll(): Promise<void> {
  await AsyncStorage.multiRemove([KEY_CURRENT_DAY, KEY_TRANSCRIPTS, KEY_MESSAGES_TODAY]);
}