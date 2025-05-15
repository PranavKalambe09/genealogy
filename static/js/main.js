// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Handle relationship selection logic
    const relationshipType = document.getElementById('relationship_type');
    const individual1 = document.getElementById('individual1');
    const individual2 = document.getElementById('individual2');
    
    // If these elements exist on the page
    if (relationshipType && individual1 && individual2) {
        // Prevent selecting the same person for both sides of a relationship
        individual1.addEventListener('change', function() {
            const selected = this.value;
            
            // Enable all options in individual2
            Array.from(individual2.options).forEach(option => {
                option.disabled = false;
            });
            
            // Disable the option in individual2 that matches the selected value in individual1
            if (selected) {
                const matchingOption = individual2.querySelector(`option[value="${selected}"]`);
                if (matchingOption) {
                    matchingOption.disabled = true;
                }
                
                // If individual2 has the same value selected, reset it
                if (individual2.value === selected) {
                    individual2.value = '';
                }
            }
        });
        
        // Do the same for individual2
        individual2.addEventListener('change', function() {
            const selected = this.value;
            
            // Enable all options in individual1
            Array.from(individual1.options).forEach(option => {
                option.disabled = false;
            });
            
            // Disable the option in individual1 that matches the selected value in individual2
            if (selected) {
                const matchingOption = individual1.querySelector(`option[value="${selected}"]`);
                if (matchingOption) {
                    matchingOption.disabled = true;
                }
                
                // If individual1 has the same value selected, reset it
                if (individual1.value === selected) {
                    individual1.value = '';
                }
            }
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});