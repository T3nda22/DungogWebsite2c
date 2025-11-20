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

    // Date calculation for rental forms with availability checking
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const daysCount = document.getElementById('days-count');
    const totalPrice = document.getElementById('total-price');
    const dateError = document.getElementById('dateError');
    const submitBtn = document.getElementById('submitBtn');
    const rentalForm = document.getElementById('rentalForm');

    if (startDateInput && endDateInput && daysCount && totalPrice) {
        const dailyRate = parseFloat(totalPrice.textContent.replace('₱', '')) || 0;
        let blockedDates = [];
        let flatpickrStart, flatpickrEnd;

        // Fetch availability data if we're on a rental page
        if (startDateInput.type === 'text' && startDateInput.readOnly) {
            // This is a Flatpickr input, initialize with availability
            initializeAvailabilityDatePickers();
        } else {
            // Regular date inputs (fallback)
            initializeBasicDatePickers();
        }

        function initializeAvailabilityDatePickers() {
            const itemId = getItemIdFromPage();
            if (itemId) {
                fetchAvailability(itemId);
            } else {
                initializeDatePickers([]);
            }
        }

        function initializeBasicDatePickers() {
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

        async function fetchAvailability(itemId) {
            try {
                const response = await fetch(`/item/${itemId}/availability`);
                const data = await response.json();
                blockedDates = data.blocked_dates.map(date => new Date(date));
                initializeDatePickers(blockedDates);
                renderCalendarPreview(blockedDates);
            } catch (error) {
                console.error('Error fetching availability:', error);
                initializeDatePickers([]);
            }
        }

        function initializeDatePickers(blockedDates) {
            // Initialize start date picker
            flatpickrStart = flatpickr(startDateInput, {
                minDate: 'today',
                dateFormat: 'Y-m-d',
                disable: blockedDates,
                onChange: function(selectedDates, dateStr, instance) {
                    if (selectedDates.length > 0) {
                        flatpickrEnd.set('minDate', selectedDates[0]);
                        const endDateValue = flatpickrEnd.selectedDates[0];
                        if (endDateValue && endDateValue < selectedDates[0]) {
                            flatpickrEnd.clear();
                        }
                        calculatePrice();
                        validateDates();
                    }
                }
            });

            // Initialize end date picker
            flatpickrEnd = flatpickr(endDateInput, {
                minDate: 'today',
                dateFormat: 'Y-m-d',
                disable: blockedDates,
                onChange: function(selectedDates, dateStr, instance) {
                    if (selectedDates.length > 0) {
                        calculatePrice();
                        validateDates();
                    }
                }
            });
        }

        function calculatePrice() {
            const start = flatpickrStart ? flatpickrStart.selectedDates[0] : new Date(startDateInput.value);
            const end = flatpickrEnd ? flatpickrEnd.selectedDates[0] : new Date(endDateInput.value);

            if (start && end) {
                const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

                if (days > 0) {
                    daysCount.textContent = days + ' day' + (days !== 1 ? 's' : '');
                    totalPrice.textContent = '₱' + (days * dailyRate).toFixed(2);
                    return;
                }
            }

            daysCount.textContent = '0 days';
            totalPrice.textContent = '₱0.00';
        }

        function validateDates() {
            if (!dateError) return;

            const start = flatpickrStart ? flatpickrStart.selectedDates[0] : new Date(startDateInput.value);
            const end = flatpickrEnd ? flatpickrEnd.selectedDates[0] : new Date(endDateInput.value);

            if (!start || !end) {
                hideError();
                return;
            }

            if (end < start) {
                showError('End date cannot be before start date');
                return;
            }

            // Check if any date in the range is blocked
            const currentDate = new Date(start);
            while (currentDate <= end) {
                const dateString = currentDate.toISOString().split('T')[0];
                if (blockedDates.some(blocked => blocked.toISOString().split('T')[0] === dateString)) {
                    showError('Selected dates include unavailable dates. Please check the calendar.');
                    return;
                }
                currentDate.setDate(currentDate.getDate() + 1);
            }

            hideError();
        }

        function showError(message) {
            if (!dateError) return;
            dateError.textContent = message;
            dateError.style.display = 'block';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.6';
            }
        }

        function hideError() {
            if (!dateError) return;
            dateError.style.display = 'none';
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
            }
        }

        function renderCalendarPreview(blockedDates) {
            const calendarEl = document.getElementById('calendarPreview');
            if (!calendarEl) return;

            const today = new Date();
            const currentMonth = today.getMonth();
            const currentYear = today.getFullYear();

            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'];

            const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
            const firstDay = new Date(currentYear, currentMonth, 1).getDay();

            let calendarHTML = `
                <div class="calendar-header">
                    <h5>${monthNames[currentMonth]} ${currentYear}</h5>
                </div>
                <div class="calendar-grid">
                    <div class="calendar-day-header">Sun</div>
                    <div class="calendar-day-header">Mon</div>
                    <div class="calendar-day-header">Tue</div>
                    <div class="calendar-day-header">Wed</div>
                    <div class="calendar-day-header">Thu</div>
                    <div class="calendar-day-header">Fri</div>
                    <div class="calendar-day-header">Sat</div>
            `;

            // Empty cells for days before the first day of the month
            for (let i = 0; i < firstDay; i++) {
                calendarHTML += '<div class="calendar-day"></div>';
            }

            // Days of the month
            for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(currentYear, currentMonth, day);
                const dateString = date.toISOString().split('T')[0];
                const isToday = day === today.getDate() && currentMonth === today.getMonth();
                const isBlocked = blockedDates.some(blocked =>
                    blocked.toISOString().split('T')[0] === dateString
                );
                const isPast = date < today;

                let dayClass = 'calendar-day';
                if (isToday) dayClass += ' today';
                if (isBlocked || isPast) {
                    dayClass += ' unavailable';
                } else {
                    dayClass += ' available';
                }

                calendarHTML += `<div class="${dayClass}">${day}</div>`;
            }

            calendarHTML += '</div>';

            // Legend
            calendarHTML += `
                <div class="availability-legend">
                    <div class="legend-item">
                        <div class="legend-color legend-available"></div>
                        <span>Available</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color legend-unavailable"></div>
                        <span>Unavailable</span>
                    </div>
                </div>
            `;

            calendarEl.innerHTML = calendarHTML;
        }

        function getItemIdFromPage() {
            // Try to get item ID from various sources
            const urlParts = window.location.pathname.split('/');
            const rentIndex = urlParts.indexOf('rent');
            if (rentIndex !== -1 && urlParts[rentIndex + 1]) {
                return parseInt(urlParts[rentIndex + 1]);
            }

            // Check for hidden input
            const itemIdInput = document.getElementById('itemId');
            if (itemIdInput) return parseInt(itemIdInput.value);

            return null;
        }

        // Form submission validation for availability
        if (rentalForm) {
            rentalForm.addEventListener('submit', function(e) {
                const start = flatpickrStart ? flatpickrStart.selectedDates[0] : new Date(startDateInput.value);
                const end = flatpickrEnd ? flatpickrEnd.selectedDates[0] : new Date(endDateInput.value);

                if (!start || !end) {
                    e.preventDefault();
                    showError('Please select both start and end dates');
                    return;
                }

                if (end < start) {
                    e.preventDefault();
                    showError('End date cannot be before start date');
                    return;
                }

                // Final validation for blocked dates
                const currentDate = new Date(start);
                while (currentDate <= end) {
                    const dateString = currentDate.toISOString().split('T')[0];
                    if (blockedDates.some(blocked => blocked.toISOString().split('T')[0] === dateString)) {
                        e.preventDefault();
                        showError('Selected dates include unavailable dates. Please choose different dates.');
                        return;
                    }
                    currentDate.setDate(currentDate.getDate() + 1);
                }
            });
        }
    }

    // Availability Management
    const availabilityPage = document.querySelector('.availability-container');
    if (availabilityPage) {
        initializeAvailabilityManagement();
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

// Availability Management Functions
function initializeAvailabilityManagement() {
    const datePicker = document.getElementById('datePicker');
    const blockDateBtn = document.getElementById('blockDateBtn');
    const unblockDateBtn = document.getElementById('unblockDateBtn');
    const itemId = document.getElementById('itemId').value;

    let selectedDates = [];

    if (datePicker) {
        // Initialize Flatpickr for multiple date selection
        const flatpickrInstance = flatpickr(datePicker, {
            mode: "multiple",
            dateFormat: "Y-m-d",
            minDate: "today",
            onChange: function(selectedDates, dateStr, instance) {
                selectedDates = selectedDates;
            }
        });

        // Block dates
        if (blockDateBtn) {
            blockDateBtn.addEventListener('click', function() {
                if (selectedDates.length === 0) {
                    showToast('Please select dates to block', 'error');
                    return;
                }

                blockDates(itemId, selectedDates);
            });
        }

        // Unblock dates
        if (unblockDateBtn) {
            unblockDateBtn.addEventListener('click', function() {
                if (selectedDates.length === 0) {
                    showToast('Please select dates to unblock', 'error');
                    return;
                }

                unblockDates(itemId, selectedDates);
            });
        }
    }

    // Add click handlers for individual unblock buttons
    document.querySelectorAll('.unblock-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const date = this.getAttribute('data-date');
            unblockDates(itemId, [new Date(date)]);
        });
    });
}

async function blockDates(itemId, dates) {
    try {
        showToast('Blocking dates...', 'info');
        const response = await fetch(`/block-date/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                dates: dates.map(date => date.toISOString().split('T')[0]),
                reason: 'owner_blocked'
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Dates blocked successfully', 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        console.error('Error blocking dates:', error);
        showToast('Error blocking dates', 'error');
    }
}

async function unblockDates(itemId, dates) {
    try {
        showToast('Unblocking dates...', 'info');
        const response = await fetch(`/unblock-date/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                dates: dates.map(date => date.toISOString().split('T')[0])
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Dates unblocked successfully', 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        console.error('Error unblocking dates:', error);
        showToast('Error unblocking dates', 'error');
    }
}

// Calendar navigation
function navigateCalendar(direction) {
    const currentMonthElem = document.getElementById('currentMonth');
    const calendarGrid = document.getElementById('calendarGrid');

    // This would typically make an AJAX call to get the next/previous month's data
    // For now, we'll just reload the page with new month parameters
    const url = new URL(window.location.href);
    const currentMonth = url.searchParams.get('month') || new Date().getMonth() + 1;
    const currentYear = url.searchParams.get('year') || new Date().getFullYear();

    let newMonth = parseInt(currentMonth);
    let newYear = parseInt(currentYear);

    if (direction === 'next') {
        newMonth++;
        if (newMonth > 12) {
            newMonth = 1;
            newYear++;
        }
    } else {
        newMonth--;
        if (newMonth < 1) {
            newMonth = 12;
            newYear--;
        }
    }

    url.searchParams.set('month', newMonth);
    url.searchParams.set('year', newYear);
    window.location.href = url.toString();
}

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