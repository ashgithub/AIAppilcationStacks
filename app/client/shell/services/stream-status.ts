export interface StreamStatusItem {
  timestamp: number;
  duration: number;
  message: string;
  type: string;
}

export interface StatusUpdateResult {
  status: StreamStatusItem[];
  totalDuration: number;
  appended: boolean;
}

export function appendStatusWithTiming(
  currentStatus: StreamStatusItem[],
  message: string,
  type: string,
  startTime: number | null,
  now: number = Date.now()
): StatusUpdateResult {
  const lastStatus = currentStatus[currentStatus.length - 1];
  const duration = lastStatus ? (now - lastStatus.timestamp) / 1000 : 0;

  if (lastStatus && lastStatus.message === message && lastStatus.type === type) {
    return {
      status: currentStatus,
      totalDuration: startTime ? (now - startTime) / 1000 : 0,
      appended: false,
    };
  }

  const nextStatus: StreamStatusItem[] = [
    ...currentStatus,
    {
      timestamp: now,
      duration,
      message,
      type,
    },
  ];

  return {
    status: nextStatus,
    totalDuration: startTime ? (now - startTime) / 1000 : 0,
    appended: true,
  };
}

export function getGenericStreamStatus(kind?: string): { message: string; type: string } | null {
  if (kind === "task") {
    return null;
  }

  if (kind === "message") {
    return { message: "Direct message received", type: "message" };
  }

  const eventKind = kind || "unknown";
  return { message: `Event type: ${eventKind}`, type: eventKind };
}
