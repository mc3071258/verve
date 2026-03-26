//Get prompt data from the DOM (passed from Django template as JSON)
//Convert the JSON string into a JavaScript array
const prompts = JSON.parse(document.getElementById("prompt-data").textContent);

//Track the current index of the prompt being displayed
let index = 0;

//Display the current prompt
function showPrompt() {
    
    //If there are no prompts, show a fallback message and clear the second option
    if (prompts.length == 0) {
        document.getElementById("optionA").innerText = "No prompts";
        document.getElementById("optionB").innerText = "";
        return;
    }

    //Split the current prompt string into two options using "|" as the separator
    const [optionA, optionB] = prompts[index].split("|");

    //Update the DOM elements with the two options
    document.getElementById("optionA").innerText = optionA.trim();
    document.getElementById("optionB").innerText = optionB.trim();
}

// Move to the next prompt in the list
function nextPrompt() {
    //Increment index and loop back to the start if at the end of the array
    index = (index + 1) % prompts.length;
    // Display the updated prompt
    showPrompt();
}
// Show the first prompt when the page loads
showPrompt();
