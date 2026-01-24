import java.util.Scanner;

public class Scgpa {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        
        System.out.println("==========================================");
        System.out.println("       SCHOLARSPACE SGPA CALCULATOR       ");
        System.out.println("==========================================");

        // 1. Ask how many subjects
        System.out.print("Enter number of subjects: ");
        int numSubjects = scanner.nextInt();

        double totalCredits = 0;
        double totalWeightedPoints = 0;

        // 2. Loop through each subject to get data
        for (int i = 1; i <= numSubjects; i++) {
            System.out.println("\nSubject " + i + ":");
            
            System.out.print("  Enter Credits (e.g., 3 or 4): ");
            double credits = scanner.nextDouble();
            
            System.out.print("  Enter Grade (O, A+, A, B+, B, C, P, F): ");
            String grade = scanner.next();
            
            double gradePoint = getGradePoint(grade);
            
            // Error check for bad grade input
            if (gradePoint == -1) {
                System.out.println("  Invalid Grade! Please enter O, A+, A, B+, etc.");
                i--; // Go back and try this subject again
                continue;
            }

            totalWeightedPoints += (credits * gradePoint);
            totalCredits += credits;
        }

        // 3. Calculate and Print Result
        if (totalCredits > 0) {
            double sgpa = totalWeightedPoints / totalCredits;
            System.out.println("\n==========================================");
            System.out.printf("  YOUR SGPA IS: %.2f\n", sgpa);
            System.out.println("==========================================");
        } else {
            System.out.println("Error: Total credits cannot be zero.");
        }
        
        scanner.close();
    }

    // Helper: Converts Letters (A, B) to Numbers (8.0, 6.0)
    public static double getGradePoint(String grade) {
        switch (grade.toUpperCase()) {
            case "O":  return 10.0;
            case "A+": return 9.0;
            case "A":  return 8.0;
            case "B+": return 7.0;
            case "B":  return 6.0;
            case "C":  return 5.0;
            case "P":  return 4.0;
            case "F":  return 0.0;
            default:   return -1.0; // Invalid grade
        }
    }
}