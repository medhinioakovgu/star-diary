// frontend/mobile/openaiClient.ts

import OpenAI from 'openai';

let _client: OpenAI | null = null;

function getClient(): OpenAI {
  if (_client) return _client;

  const apiKey = process.env.EXPO_PUBLIC_OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error(
      'EXPO_PUBLIC_OPENAI_API_KEY not set. Check your .env file ' +
      'and restart the Expo dev server (env vars are baked at bundle time).'
    );
  }

  _client = new OpenAI({
    apiKey,
    dangerouslyAllowBrowser: true,
  });
  return _client;
}

/**
 * Run a single LLM call with a system prompt and one user message.
 * Used by the chatbot, the daily state updater, and the magazine renderer.
 *
 * Token budgets and temperature match research/pipelines.py exactly:
 *   - chatbot:        max_tokens=512,  temperature=0.7
 *   - state update:   max_tokens=900,  temperature=0.7
 *   - magazine render: max_tokens=1000, temperature=0.7
 */
export async function callLLM(params: {
  systemPrompt: string;
  userContent: string;
  maxTokens: number;
  temperature?: number;
  model?: string;
}): Promise<string> {
  const {
    systemPrompt,
    userContent,
    maxTokens,
    temperature = 0.7,
    model = 'gpt-4o-mini',
  } = params;

  const client = getClient();
  const response = await client.chat.completions.create({
    model,
    temperature,
    max_tokens: maxTokens,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userContent },
    ],
  });

  const text = response.choices[0]?.message?.content;
  if (!text) {
    throw new Error('OpenAI returned empty response');
  }
  return text;
}