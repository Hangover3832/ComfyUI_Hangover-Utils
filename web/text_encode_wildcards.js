// Companion JS for the TextEncodeWildcards node.
// Adds an "Apply to prompt" button to the node. Clicking it inserts the
// currently selected wildcard (wrapped in curly braces) into the prompt box,
// at the cursor position when reachable, otherwise appended.

const WILDCARD_WIDGET = "wildcards";
const PROMPT_WIDGET = "prompt";
const PLACEHOLDER = "wildcards...";
const BUTTON_NAME = "Apply to prompt";

//const { app } = window.comfyAPI.app;
import { app } from "/scripts/app.js";

// Compare node names ignoring whitespace/case, so "Text Encode Wildcards",
// "Text Encode Wild cards" and "TextEncodeWildcards" all match.
function normalizeName(name) {
    return (name || "").replace(/\s+/g, "").toLowerCase();
}

const TARGET_NAME = normalizeName("TextEncodeWildcards");

// node.widgets is a flat, per-instance list of widget objects ({name, value,
// el, ...}). Find the widgets we care about by name.
function findWidget(node, name) {
    const widgets = node.widgets;
    for (let i = 0; i < widgets?.length; i++) {
        if (widgets[i] && widgets[i].name === name) return widgets[i];
    }
    return null;
}

// Get the prompt textarea, or null if it can't be reached. The widget's el may
// be the textarea itself or a wrapper around it.
function getPromptTextarea(node) {
    const el = findWidget(node, PROMPT_WIDGET)?.el;
    if (!el) return null;
    if (el.tagName === "TEXTAREA") return el;
    if (el.querySelector) return el.querySelector("textarea");
    return null;
}

function insertIntoPrompt(node, insertion) {
    const prompt = findWidget(node, PROMPT_WIDGET);
    const ta = getPromptTextarea(node);
    if (!ta) {
        prompt.value = (prompt.value ?? "") + insertion;
        return;
    }

    const base = ta.value;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const newValue = base.slice(0, start) + insertion + base.slice(end);
    ta.value = newValue;
    prompt.value = newValue;

    const pos = start + insertion.length;
    ta.selectionStart = ta.selectionEnd = pos;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
}

function addButton(node) {
    const combo = findWidget(node, WILDCARD_WIDGET);
    const prompt = findWidget(node, PROMPT_WIDGET);
    if (!combo || !prompt) return;

    // Skip if this node already has the button (onNodeCreated may run more
    // than once per instance).
    if (node.widgets.some((w) => w.name === BUTTON_NAME)) return;

    node.addWidget(
        "button",
        BUTTON_NAME,
        "",
        function () {
            const value = combo.value;
            if (!value || value === PLACEHOLDER) return;
            insertIntoPrompt(node, `{${value}}`);
        },
        { serialize: false }
    );
}

app.registerExtension({
    name: "Hangover.Wildcards",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (normalizeName(nodeData.name) !== TARGET_NAME) return;

        // Patch the node type's onNodeCreated so the button is added for every
        // instance of this node. This is the same pattern other custom nodes
        // (e.g. Ollama) use to add buttons to a specific node type.
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (originalOnNodeCreated) originalOnNodeCreated.apply(this, arguments);
            addButton(this);
        };
    },
});
