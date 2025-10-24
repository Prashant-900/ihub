import { sendTrigger, changeExpression } from './index';
import { expressionMap } from '../constants';

// Keep track of scheduled timers so we can cancel previous timelines
let _scheduledTimers = [];

function _clearScheduled() {
  for (const t of _scheduledTimers) {
    clearTimeout(t);
  }
  _scheduledTimers = [];
}

/**
 * Execute animation timeline from backend
 * @param {Array} timeline - Array of timeline entries with timing and animations
 */
/**
 * Execute animation timeline from backend
 * @param {Array} timeline - Array of timeline entries with timing and animations
 * @param {Object} [opts] - Options
 * @param {number} [opts.startAt] - Optional AudioContext time (in seconds) that should be used as the timeline start reference.
 */
export function executeAnimationTimeline(timeline, opts = {}) {
  if (!timeline) return;

  // support payloads where timeline might be wrapped: { timeline: [...] }
  if (!Array.isArray(timeline) && timeline.timeline && Array.isArray(timeline.timeline)) {
    timeline = timeline.timeline;
  }
  if (!Array.isArray(timeline)) return;

  // clear any previously scheduled timers to avoid overlapping timelines
  _clearScheduled();

  // Get a shared AudioContext to compute current time. This allows callers to pass a startAt using the same clock.
  const AudioCtx = window.__globalAudioContext || (window.AudioContext || window.webkitAudioContext);
  const audioCtx = window.__globalAudioContext || new AudioCtx();
  window.__globalAudioContext = audioCtx;

  // compute total duration for promise resolution (we'll compute delays relative to the shared audio clock)
  let maxTimeMs = 0;
  // determine base offset: if opts.startAt is provided it represents the audioCtx.currentTime at which timeline time=0 should start
  const startAt = typeof opts.startAt === 'number' ? opts.startAt : audioCtx.currentTime;
  const baseOffsetSec = Math.max(0, startAt - audioCtx.currentTime);
  timeline.forEach((entry) => {
    const tMs = Math.max(0, ( (entry.time || 0) + baseOffsetSec) * 1000);
    if (tMs > maxTimeMs) maxTimeMs = tMs;
  });

  return new Promise((resolve) => {
    timeline.forEach((entry) => {
  // schedule event at: (startAt + entry.time)
  const timeMs = Math.max(0, ( (entry.time || 0) + baseOffsetSec) * 1000);
    const triggerSpeed = entry.trigger_speed || 1.0;

    // Schedule expressions
    if (entry.expressions && Array.isArray(entry.expressions)) {
      entry.expressions.forEach((expressionName) => {
        const t = setTimeout(() => {
          try {
            const exprId = expressionMap[expressionName];
            if (exprId !== undefined) {
              changeExpression(exprId);
            }
          } catch {
            void 0;
          }
        }, timeMs);
        _scheduledTimers.push(t);
      });
    }

    // Schedule triggers with speed
    if (entry.triggers && Array.isArray(entry.triggers)) {
      entry.triggers.forEach((triggerName) => {
        const t = setTimeout(() => {
          try {
            sendTrigger(triggerName, triggerSpeed);
          } catch {
            void 0;
          }
        }, timeMs);
        _scheduledTimers.push(t);
      });
    }
    });

    // schedule resolver a bit after the last event
    const endTimer = setTimeout(() => {
      _clearScheduled();
      resolve();
    }, maxTimeMs + 80);
    _scheduledTimers.push(endTimer);
  });
}



export default {
  executeAnimationTimeline,
  clearScheduled: _clearScheduled,
};
