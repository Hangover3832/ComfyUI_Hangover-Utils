// Companion JS for the SympyInterpreter node.
// Shows the evaluated expression (str_A) as a text widget on the node.
// The Python side sends the result via ui.PreviewText, which arrives in the
// node executed message as message.text.

import { app } from "/scripts/app.js";

// Compare node names ignoring whitespace/case, so "Sympy Interpreter" and
// "SympyInterpreter" both match.
function normalizeName(name) {
    return (name || "").replace(/\s+/g, "").toLowerCase();
}

const TARGET_NAME = normalizeName("SympyInterpreter");
const RESULT_WIDGET = "result";

// node.widgets is a flat, per-instance list of widget objects ({name, value,
// el, ...}). Find the result widget by name.
function findWidget(node, name) {
    const widgets = node.widgets;
    for (let i = 0; i < widgets?.length; i++) {
        if (widgets[i] && widgets[i].name === name) return widgets[i];
    }
    return null;
}

// message.text is the ui payload sent by the server: an array of strings.
function resultText(message) {
    const text = message?.text;
    if (!text) return "";
    if (Array.isArray(text)) return text.filter((t) => t != null).join("  ");
    return String(text);
}

function addResultWidget(node) {
    // Skip if this node already has the widget (onNodeCreated may run more
    // than once per instance).
    if (node.widgets.some((w) => w.name === RESULT_WIDGET)) return;

    const el = document.createElement("div");
    el.textContent = "";
    const widget = node.addDOMWidget(RESULT_WIDGET, "result", el);
    widget.serialize = false;
}

function updateResultWidget(node, message) {
    // DOM widgets expose the element as .element in the new frontend (.el is
    // the old-frontend convention).
    const widget = findWidget(node, RESULT_WIDGET);
    const el = widget?.element ?? widget?.el;
    if (!el) return;
    el.textContent = resultText(message);
}

app.registerExtension({
    name: "Hangover.SympyResult",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (normalizeName(nodeData.name) !== TARGET_NAME) return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (originalOnNodeCreated) originalOnNodeCreated.apply(this, arguments);
            addResultWidget(this);
        };

        // The server sends an executed message with the node ui output
        // ({ text: [...] }) whenever the node runs or its result is cached.
        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            if (originalOnExecuted) originalOnExecuted.apply(this, [message]);
            updateResultWidget(this, message);
        };
    },
});
