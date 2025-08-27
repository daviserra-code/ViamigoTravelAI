function showSuccessPopup(message, redirectUrl) {
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';
    
    const popup = document.createElement('div');
    popup.className = 'bg-gray-800 rounded-xl p-6 mx-4 max-w-sm w-full border border-gray-600';
    popup.innerHTML = `
        <div class="text-center">
            <div class="text-4xl mb-4">✅</div>
            <h3 class="text-white font-semibold mb-2">${message}</h3>
            <p class="text-gray-400 text-sm mb-4">Verrai reindirizzato alla pagina di login</p>
            <button onclick="proceedToLogin()" class="w-full bg-gradient-to-r from-violet-600 to-purple-600 text-white py-2 rounded-lg font-medium hover:from-violet-700 hover:to-purple-700">
                Continua
            </button>
        </div>
    `;
    
    overlay.appendChild(popup);
    document.body.appendChild(overlay);
    
    setTimeout(() => { window.location.href = redirectUrl; }, 3000);
    window.proceedToLogin = function() { window.location.href = redirectUrl; };
}