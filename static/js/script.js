// Toast notifications auto-hide
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide toast messages after 5 seconds
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        if (toast.classList.contains('show')) {
            setTimeout(() => {
                toast.classList.remove('show');
            }, 5000);
        }
    });

    // Payment method selection
    const paymentMethods = document.querySelectorAll('input[name="payment_method"]');
    const gcashInstructions = document.getElementById('gcashInstructions');

    if (paymentMethods && gcashInstructions) {
        paymentMethods.forEach(method => {
            method.addEventListener('change', function() {
                if (this.value === 'gcash') {
                    gcashInstructions.style.display = 'block';
                } else {
                    gcashInstructions.style.display = 'none';
                }
            });
        });
    }

    // Date calculation for rental forms
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const daysCount = document.getElementById('days-count');
    const totalPrice = document.getElementById('total-price');

    if (startDateInput && endDateInput && daysCount && totalPrice) {
        const dailyRate = parseFloat(totalPrice.textContent.replace('₱', '')) || 0;

        function calculatePrice() {
            if (startDateInput.value && endDateInput.value) {
                const start = new Date(startDateInput.value);
                const end = new Date(endDateInput.value);
                const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

                if (days > 0) {
                    daysCount.textContent = days + ' day' + (days !== 1 ? 's' : '');
                    totalPrice.textContent = '₱' + (days * dailyRate).toFixed(2);
                } else {
                    daysCount.textContent = '0 days';
                    totalPrice.textContent = '₱0.00';
                }
            }
        }

        startDateInput.addEventListener('change', function() {
            endDateInput.min = this.value;
            calculatePrice();
        });

        endDateInput.addEventListener('change', calculatePrice);

        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        startDateInput.min = today;
        endDateInput.min = today;
    }

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.style.borderColor = 'var(--accent)';
                } else {
                    field.style.borderColor = '';
                }
            });

            if (!valid) {
                e.preventDefault();
                showToast('Please fill in all required fields.', 'error');
            }
        });
    });

    // Search functionality enhancement
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // Could add debounced search here in the future
        });
    }
});

// Utility function to show toast messages
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} show`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 5000);
}

// Image error handling
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.src = '/static/images/default-item.jpg';
        });
    });
});