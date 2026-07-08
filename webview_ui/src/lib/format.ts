export function formatDurationMs(milliseconds: number): string {
  if (!Number.isFinite(milliseconds) || milliseconds <= 0) {
    return "0s";
  }

  const totalSeconds = milliseconds / 1000;
  if (totalSeconds < 60) {
    return `${formatSeconds(totalSeconds)}s`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.round(totalSeconds % 60);
  if (seconds === 60) {
    return `${minutes + 1}m 00s`;
  }
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

export function formatCount(count: number): string {
  if (!Number.isFinite(count) || count <= 0) {
    return "0";
  }
  return Math.trunc(count).toLocaleString();
}

export function formatDateLabel(dateLabel: string): string {
  if (!dateLabel) {
    return "Today";
  }
  return `Today, ${dateLabel}`;
}

function formatSeconds(seconds: number): string {
  if (seconds >= 10 || Number.isInteger(seconds)) {
    return Math.round(seconds).toString();
  }
  return seconds.toFixed(1);
}
