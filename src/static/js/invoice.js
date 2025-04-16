document.addEventListener("DOMContentLoaded", function () {
    const formFields = {
        rent: document.getElementById("id_rent_amount"),
        parking: document.getElementById("id_parking_fee"),
        electricity: document.getElementById("id_electricity_fee"),
        drinkingWater: document.getElementById("id_drinking_water_fee"),
        normalWater: document.getElementById("id_normal_water_fee"),
        waste: document.getElementById("id_waste_fee"),
        security: document.getElementById("id_security_fee"),
        generator: document.getElementById("id_generator_power_backup_fee"),
        internet: document.getElementById("id_internet_telephone_tv_fee"),
        other: document.getElementById("id_other_fee"),
        discount: document.getElementById("id_discount"),
        total: document.getElementById("id_total_amount"),
        tax: document.getElementById("id_tax"),
        grand: document.getElementById("id_grand_total"),
        previousDue: document.getElementById("id_previous_due"),
    };

    function parseValue(input) {
        return parseFloat(input?.value) || 0;
    }

    function calculateTotals() {
        let sum = (
            parseValue(formFields.rent) +
            parseValue(formFields.parking) +
            parseValue(formFields.electricity) +
            parseValue(formFields.drinkingWater) +
            parseValue(formFields.normalWater) +
            parseValue(formFields.waste) +
            parseValue(formFields.security) +
            parseValue(formFields.generator) +
            parseValue(formFields.internet) +
            parseValue(formFields.other)
        );

        const discount = parseValue(formFields.discount);
        const tax = parseValue(formFields.tax);
        const previousDue = parseValue(formFields.previousDue);

        const total = sum ;
        const grandTotal = total + tax + previousDue - discount;

        formFields.total.value = total.toFixed(2);
        formFields.grand.value = grandTotal.toFixed(2);
    }

    // Add input event listeners to relevant fields
    for (let key in formFields) {
        if (key !== "total" && key !== "grand") {
            formFields[key]?.addEventListener("input", calculateTotals);
        }
    }

    calculateTotals(); // Initial calculation on page load
});
