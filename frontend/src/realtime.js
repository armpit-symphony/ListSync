import { apiBaseUrl } from './api';

export function subscribeToHouseholdEvents({ onEvent, onStatus }) {
  const controller = new AbortController();
  let stopped = false;
  let retryMs = 500;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function connect() {
    while (!stopped) {
      onStatus?.('connecting');
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${apiBaseUrl()}/api/events`, {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'text/event-stream',
          },
          signal: controller.signal,
        });
        if (!response.ok || !response.body) {
          throw new Error(`Event stream failed (${response.status})`);
        }
        retryMs = 500;
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (!stopped) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split('\n\n');
          buffer = frames.pop() || '';
          for (const frame of frames) {
            const dataLine = frame
              .split('\n')
              .filter((line) => line.startsWith('data:'))
              .map((line) => line.slice(5).trim())
              .join('');
            if (!dataLine) continue;
            let event;
            try {
              event = JSON.parse(dataLine);
            } catch (err) {
              continue;
            }
            if (event.type === 'ready') {
              onStatus?.('live');
            }
            onEvent?.(event);
          }
        }
      } catch (err) {
        if (stopped || err.name === 'AbortError') return;
      }
      if (stopped) return;
      onStatus?.('reconnecting');
      await sleep(retryMs);
      retryMs = Math.min(retryMs * 2, 8000);
    }
  }

  connect();
  return () => {
    stopped = true;
    controller.abort();
  };
}
