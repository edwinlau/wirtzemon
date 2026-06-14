/**
 * Prompted question bank (Phase 5). Stored here as typed JSON so it can be
 * filtered by room type during the inspection capture flow.
 */
export interface PromptedQuestion {
  key: string;
  /** Room type this applies to. 'any' = all rooms, 'general' = inspection-level. */
  room: string;
  question: string;
  /** Optional fixed-choice answers; absence implies free text / yes-no. */
  options?: string[];
}

export const QUESTION_BANK: PromptedQuestion[] = [
  { key: 'room_size', room: 'any', question: 'Does the room feel as large as the floor plan suggests?' },
  { key: 'natural_light', room: 'any', question: 'Is there good natural light?' },
  { key: 'separate_dining', room: 'living', question: 'Is there a separate dining area?' },
  { key: 'street_noise', room: 'living', question: 'How is the street noise?' },
  { key: 'storage', room: 'any', question: 'Is storage adequate?' },
  { key: 'kitchen_match', room: 'kitchen', question: 'Does the kitchen match the listing photos?' },
  { key: 'water_pressure', room: 'bathroom', question: 'Did you check the water pressure?' },
  { key: 'sunlight_outdoor', room: 'outdoor', question: 'Does the outdoor area get good sunlight?' },
  { key: 'crowd_level', room: 'general', question: 'How busy was the open home?', options: ['Quiet', 'Moderate', 'Packed'] },
];

/** Questions that apply to a given room type (includes 'any'). */
export function questionsForRoom(roomType: string): PromptedQuestion[] {
  const t = roomType.toLowerCase();
  return QUESTION_BANK.filter((q) => q.room === 'any' || q.room === t);
}
