/**
 * Custom handler for rg tool messages
 * Uses drawProcessStep with code='RIP'
 */
import { drawProcessStep, cleanStepTitle } from "/js/messages.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";
import { ttsService } from "/js/tts-service.js";
import { createActionButton } from "/components/messages/action-buttons/simple-action-buttons.js";

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
}

function buildDetailPayload(args, opts) {
  return { ...args, ...opts };
}

export default function (extData) {
  if (extData.type !== "rg") return;

  extData.handler = function ({ id, content, kvps, heading, timestamp, agentno = 0, ...rest }) {
    const title = cleanStepTitle(heading);
    const displayKvps = { ...kvps };
    // Remove tool field from display
    delete displayKvps._tool_name;

    // Stock A0 buttons
    const contentText = String(content ?? "");
    const actionButtons = contentText.trim()
      ? [
        createActionButton("detail", "", () =>
          stepDetailStore.showStepDetail(
            buildDetailPayload(arguments[0], { headerLabels: [] })
          )
        ),
        createActionButton("speak", "", () => ttsService.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ]
      : [];

    return drawProcessStep({
      id,
      title,
      code: "RIP",
      classes: ["RIP"],
      kvps: displayKvps,
      content,
      actionButtons,
      log: arguments[0],
    });
  };
}
