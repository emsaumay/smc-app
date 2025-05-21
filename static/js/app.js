// JavaScript for Sales & Inventory Management System

$(document).ready(function() {
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Form validation
    $('form').submit(function() {
        var submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true);
        submitBtn.html('<i class="fas fa-spinner fa-spin me-2"></i>Processing...');
    });

    // Stock query functionality (AJAX)
    $('#stock-query').on('input', function() {
        var query = $(this).val();
        if (query.length > 2) {
            $.ajax({
                url: '/stock/query/',
                data: {
                    'query': query
                },
                success: function(data) {
                    displayStockResults(data.results);
                }
            });
        } else {
            $('#stock-results').empty();
        }
    });

    function displayStockResults(results) {
        var html = '';
        if (results.length > 0) {
            html = '<div class="list-group">';
            results.forEach(function(item) {
                html += '<div class="list-group-item">';
                html += '<div class="d-flex w-100 justify-content-between">';
                html += '<h6 class="mb-1">' + item.product_name + '</h6>';
                html += '<small>Qty: ' + item.quantity + '</small>';
                html += '</div>';
                html += '<p class="mb-1">Price: $' + item.price.toFixed(2);
                if (item.supplier) {
                    html += ' | Supplier: ' + item.supplier;
                }
                html += '</p>';
                if (item.sku) {
                    html += '<small>SKU: ' + item.sku + '</small>';
                }
                html += '</div>';
            });
            html += '</div>';
        } else {
            html = '<div class="alert alert-info">No products found matching your search.</div>';
        }
        $('#stock-results').html(html);
    }

    // Confirm delete actions
    $('.delete-btn').click(function(e) {
        e.preventDefault();
        var url = $(this).attr('href');
        var itemName = $(this).data('item-name');
        
        if (confirm('Are you sure you want to delete "' + itemName + '"? This action cannot be undone.')) {
            window.location.href = url;
        }
    });

    // Table row highlighting on hover
    $('.table tbody tr').hover(
        function() {
            $(this).addClass('table-active');
        },
        function() {
            $(this).removeClass('table-active');
        }
    );

    // Auto-calculate sale total
    $('#id_quantity_sold, #id_unit_price').on('input', function() {
        var quantity = parseFloat($('#id_quantity_sold').val()) || 0;
        var price = parseFloat($('#id_unit_price').val()) || 0;
        var total = quantity * price;
        $('#sale-total-display').text('Total: $' + total.toFixed(2));
    });

    // Stock level warnings
    $('.stock-quantity').each(function() {
        var quantity = parseInt($(this).text());
        var minStock = parseInt($(this).data('min-stock')) || 0;
        
        if (quantity <= minStock) {
            $(this).closest('tr').addClass('low-stock-row');
        }
    });

    // File upload progress
    $('input[type="file"]').change(function() {
        var fileName = $(this).val().split('\\').pop();
        $(this).next('.form-text').html('<i class="fas fa-file me-2"></i>' + fileName);
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Dark mode toggle (future feature)
    $('.dark-mode-toggle').click(function() {
        $('body').toggleClass('dark-mode');
        localStorage.setItem('darkMode', $('body').hasClass('dark-mode'));
    });

    // Load dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        $('body').addClass('dark-mode');
    }

    // Print functionality
    $('.print-btn').click(function() {
        window.print();
    });

    // Export functionality
    $('.export-btn').click(function() {
        var table = $(this).data('table');
        exportTableToCSV(table);
    });

    function exportTableToCSV(tableId) {
        var csv = [];
        var rows = document.querySelectorAll(tableId + " tr");
        
        for (var i = 0; i < rows.length; i++) {
            var row = [], cols = rows[i].querySelectorAll("td, th");
            
            for (var j = 0; j < cols.length; j++) {
                row.push(cols[j].innerText);
            }
            
            csv.push(row.join(","));
        }
        
        downloadCSV(csv.join("\n"), "export.csv");
    }

    function downloadCSV(csv, filename) {
        var csvFile;
        var downloadLink;
        
        csvFile = new Blob([csv], {type: "text/csv"});
        downloadLink = document.createElement("a");
        downloadLink.download = filename;
        downloadLink.href = window.URL.createObjectURL(csvFile);
        downloadLink.style.display = "none";
        document.body.appendChild(downloadLink);
        downloadLink.click();
    }
});

// Service Worker Registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/pwa/service-worker.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            }, function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Install PWA prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later.
    deferredPrompt = e;
    // Show install button
    $('.install-app-btn').show();
});

$('.install-app-btn').click(function() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the A2HS prompt');
            }
            deferredPrompt = null;
        });
    }
});