import { sendTrigger, changeExpression } from './index';
import { expressionMap } from '../constants';

/**
 * Execute animation timeline from backend
 * @param {Array} timeline - Array of timeline entries with timing and animations
 */
export function executeAnimationTimeline(timeline) {
  if (!timeline || !Array.isArray(timeline)) return;

  timeline.forEach((entry) => {
    const timeMs = (entry.time || 0) * 1000;
    const triggerSpeed = entry.trigger_speed || 1.0;

    // Schedule expressions
    if (entry.expressions && Array.isArray(entry.expressions)) {
      entry.expressions.forEach((expressionName) => {
        setTimeout(() => {
          console.log(`[AnimController] Changing expression to: ${expressionName}`);
          const exprId = expressionMap[expressionName];
          if (exprId !== undefined) {
            changeExpression(exprId);
          }
        }, timeMs);
      });
    }

    // Schedule triggers with speed
    if (entry.triggers && Array.isArray(entry.triggers)) {
      entry.triggers.forEach((triggerName) => {
        setTimeout(() => {
          console.log(`[AnimController] Triggering: ${triggerName} with speed ${triggerSpeed}`);
          sendTrigger(triggerName, triggerSpeed);
        }, timeMs);
      });
    }

  });
}



export default {
  executeAnimationTimeline
};
