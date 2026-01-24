function calculateSGPA() {
    console.log("Starting SGPA calculation...");
    const credits = [4, 3, 4, 3, 4, 2, 1, 1, 1, 1];
    let totalCreditPoints = 0;
    let totalCredits = 0;
    let totalMarksObtained = 0;
    let fullMarks = 0;

    for (let i = 1; i <= 9; i++) {
      console.log(`Processing subject ${i}...`);
      const internal = parseInt(
        document.getElementById(`sub${i}Internal`).value
      );
      const external = parseInt(
        document.getElementById(`sub${i}External`).value
      );

      console.log(
        `Subject ${i} - Internal Marks: ${internal}, External Marks: ${external}`
      );

      if (internal < 22 || external < 18) {
        alert(`Subject ${i} failed!`);
        console.log(`Subject ${i} failed due to insufficient marks.`);
        return;
      }

      const totalMarks = internal + external;
      console.log(`Subject ${i} - Total Marks: ${totalMarks}`);

      totalMarksObtained += totalMarks;
      fullMarks += 100;

      const grade = calculateGrade(totalMarks);
      console.log(`Subject ${i} - Grade: ${grade}`);

      totalCreditPoints += grade * credits[i - 1];
      totalCredits += credits[i - 1];
    }

    const gpMarks = parseInt(document.getElementById("gpMarks").value);
    console.log(`General Proficiency Marks: ${gpMarks}`);

    if (gpMarks < 40) {
      alert("Failed in General Proficiency!");
      console.log("Failed in General Proficiency.");
      return;
    }

    totalMarksObtained += gpMarks;
    fullMarks += 100;

    const gpGrade = calculateGrade(gpMarks);
    console.log(`General Proficiency Grade: ${gpGrade}`);

    totalCreditPoints += gpGrade * credits[9];
    totalCredits += credits[9];

    const sgpa = (totalCreditPoints / totalCredits).toFixed(2);
    const percentage = ((totalMarksObtained / fullMarks) * 100).toFixed(2);

    console.log(`SGPA: ${sgpa}, Percentage: ${percentage}%`);

    const resultDiv = document.getElementById("result");
    resultDiv.style.display = "block";
    resultDiv.innerHTML = `<strong>Your SGPA is: ${sgpa}</strong>`;

    const additionalInfoDiv = document.getElementById("additionalInfo");
    additionalInfoDiv.innerHTML = `
    <p>Total Marks Obtained: ${totalMarksObtained} / ${fullMarks}</p>
    <p>Percentage: ${percentage}%</p>
  `;
  }

  function calculateGrade(marks) {
    console.log(`Calculating grade for marks: ${marks}`);
    if (marks >= 90) return 10;
    if (marks >= 75) return 9;
    if (marks >= 60) return 8;
    if (marks >= 55) return 7;
    if (marks >= 50) return 6;
    if (marks >= 45) return 5;
    if (marks >= 40) return 4;
    return 0;
  }