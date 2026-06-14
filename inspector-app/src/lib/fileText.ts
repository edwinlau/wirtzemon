import { Platform } from 'react-native';

/**
 * Read a picked file's text content across platforms. On native we use
 * expo-file-system; on web the picker hands back a blob URL that fetch() reads.
 */
export async function readFileText(uri: string): Promise<string> {
  if (Platform.OS === 'web') {
    const res = await fetch(uri);
    return res.text();
  }
  // Lazy-require so web bundles don't pull native-only modules.
  const FileSystem = require('expo-file-system') as typeof import('expo-file-system');
  return FileSystem.readAsStringAsync(uri);
}
