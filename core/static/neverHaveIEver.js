// Get prompt data from the DOM (passed from Django template as JSON)
// Convert the JSON string into a JavaScript array
const prompts = JSON.parse(document.getElementById("prompt-data").textContent);

//track the current index of the prompt being displayed
let index = 0;

//display the current prompt
function showPrompt() {
    //Set the text content to the current prompt
    //If no prompts exist, show a fallback message
    document.getElementById("prompt").innerText = prompts[index] || "There are no prompts created";
}

//Move to the next prompt in the list
function nextPrompt() {
    //Increment index and loop back to the start if at the end of the array
    index = (index + 1) % prompts.length;
    //Display the updated prompt
    showPrompt();
}

//Show the first prompt when the page loads
showPrompt();