export interface ReviewStats {
  dateLabel: string;
  dayStartMs: number;
  dayEndMs: number;
  reviewCount: number;
  distinctCardCount: number;
  totalAnswerTimeMs: number;
  averagePerCardMs: number;
  averagePerAnswerMs: number;
}

declare global {
  interface Window {
    __INITIAL_STATE__?: ReviewStats;
  }
}

export const FALLBACK_STATE: ReviewStats = {
  dateLabel: new Date().toISOString().slice(0, 10),
  dayStartMs: 0,
  dayEndMs: 0,
  reviewCount: 0,
  distinctCardCount: 0,
  totalAnswerTimeMs: 0,
  averagePerCardMs: 0,
  averagePerAnswerMs: 0
};

export function getInitialState(): ReviewStats {
  return window.__INITIAL_STATE__ ?? FALLBACK_STATE;
}
