//Get prompt data from the DOM (passed from Django template as JSON)
//convert JSON strings into JavaScript arrays
const truth_prompts = JSON.parse(document.getElementById("truth-prompt-data").textContent);
const dare_prompts = JSON.parse(document.getElementById("dare-prompt-data").textContent);

//Track current index for each prompt type.
let truth_index = 0;
let dare_index = 0

let showingPrompt = false;  //at start of game no promt yet

// Display a truth prompt
function showTruthPrompt() {
    // Set the text content to the current truth prompt
    // If no prompts exist, show a fallback message
    document.getElementById("truth_prompt").innerText = truth_prompts[truth_index] || "There are no Truth Prompts Created";
    //mark that a prompt is now being shown.
    showingPrompt = true;
}

// Display a truth prompt, same logic as displaying a truth prompt but for dare.
function showDarePrompt() {
    document.getElementById("dare_prompt").innerText = dare_prompts[dare_index] || "There are No Dare Prompts Created";
    showingPrompt = true;
}

function nextTruthPrompt() {
    //if a prompt is already showing, reset instead of advancing.
    if (showingPrompt) {
        resetPrompts();
        return;
    } else {
        //show current prompt
        showTruthPrompt();

        //move to next index, looping back to start if at the end.
        truth_index = (truth_index + 1) % truth_prompts.length;
    }
}


function nextDarePrompt() {
    //same logic as nextTruthPrompt() but for dares.
    if (showingPrompt) {
        resetPrompts();
        return;
    } else {
        showDarePrompt();
        dare_index = (dare_index + 1) % dare_prompts.length;
    }
}

//reset both prompt displays back to default text.
function resetPrompts() {
    if (showingPrompt) {
        document.getElementById("truth_prompt").innerText = "Click for truth";
        document.getElementById("dare_prompt").innerText = "Click for dare";
        //mark that no prompt is currently being shown.
        showingPrompt = false;
    }
}

