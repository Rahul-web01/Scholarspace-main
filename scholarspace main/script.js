// This function sends you from the Home Page to the Course Page
function redirectToSGPACalculator() {
    window.location.href = "selectcourse.html";
}

// This function calculates the math
function calculateSGPA() {
    let credits = document.getElementsByClassName("credit");
    let grades = document.getElementsByClassName("grade");
    let totalPoints = 0;
    let totalCredits = 0;

    for(let i = 0; i < credits.length; i++) {
        let c = parseFloat(credits[i].value);
        let g = parseFloat(grades[i].value);
        
        // Only calculate if the user typed a number
        if(!isNaN(c)) {
            totalCredits += c;
            totalPoints += (c * g);
        }
    }

    if(totalCredits === 0) {
        document.getElementById("result").innerText = "Please enter credits!";
    } else {
        let sgpa = totalPoints / totalCredits;
        document.getElementById("result").innerText = "Your SGPA: " + sgpa.toFixed(2);
    }
}