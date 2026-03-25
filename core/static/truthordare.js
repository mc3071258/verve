
const truth_prompts = JSON.parse(document.getElementById("truth-prompt-data").textContent);
const dare_prompts = JSON.parse(document.getElementById("dare-prompt-data").textContent);

let truth_index = 0;
let dare_index = 0

let showingPrompt = false;  //at start of game no promt yet

function showTruthPrompt() {
    document.getElementById("truth_prompt").innerText = truth_prompts[truth_index] || "There are no Truth Prompts Created";
    showingPrompt = true;
}

function showDarePrompt() {
    document.getElementById("dare_prompt").innerText = dare_prompts[dare_index] || "There are No Dare Prompts Created";
    showingPrompt = true;
}

function nextTruthPrompt() {
    if (showingPrompt) {
        resetPrompts();
        return;
    } else {
        showTruthPrompt();
        truth_index = (truth_index + 1) % truth_prompts.length;
    }
}
function nextDarePrompt() {
    if (showingPrompt) {
        resetPrompts();
        return;
    } else {
        showDarePrompt();
        dare_index = (dare_index + 1) % dare_prompts.length;
    }
}

function resetPrompts() {
    if (showingPrompt) {
        document.getElementById("truth_prompt").innerText = "Click for truth";
        document.getElementById("dare_prompt").innerText = "Click for dare";
        showingPrompt = false;
    }
}

