(function() {
    // Yacht 5 Offerte Tool Embed Script
    const WOWOfferte = {
        config: {
            buttonText: "OFFERTE AANVRAGEN",
            buttonColor: "#C8A84B",
            apiUrl: window.location.origin // Default to the script's origin
        },

        init: function(userConfig) {
            this.config = { ...this.config, ...userConfig };
            this.injectStyles();
            this.createButton();
            this.createModal();
        },

        injectStyles: function() {
            const css = `
                @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600&display=swap');

                .wow-offerte-btn {
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    background-color: ${this.config.buttonColor};
                    color: #2A2A12;
                    padding: 15px 28px;
                    border-radius: 3px;
                    font-family: 'Montserrat', 'Helvetica Neue', sans-serif;
                    font-weight: 600;
                    font-size: 12px;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                    cursor: pointer;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.25);
                    transition: all 0.3s ease;
                    z-index: 9999;
                    border: none;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .wow-offerte-btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 12px 35px rgba(0,0,0,0.35);
                    background-color: #B8943A;
                }
                .wow-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(42, 42, 18, 0.85);
                    backdrop-filter: blur(6px);
                    display: none;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }
                .wow-modal-container {
                    width: 90%;
                    max-width: 650px;
                    height: 85vh;
                    background: #4A4A28;
                    border-radius: 6px;
                    border: 1px solid rgba(200, 168, 75, 0.25);
                    position: relative;
                    overflow: hidden;
                    transform: scale(0.95) translateY(10px);
                    transition: transform 0.3s ease, opacity 0.3s ease;
                    box-shadow: 0 30px 80px rgba(0,0,0,0.5);
                }
                .wow-modal-overlay.active {
                    display: flex;
                    opacity: 1;
                }
                .wow-modal-overlay.active .wow-modal-container {
                    transform: scale(1) translateY(0);
                }
                .wow-modal-close {
                    position: absolute;
                    top: 18px;
                    right: 22px;
                    font-size: 22px;
                    color: rgba(200, 168, 75, 0.7);
                    cursor: pointer;
                    z-index: 10001;
                    line-height: 1;
                    transition: color 0.2s;
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 300;
                }
                .wow-modal-close:hover {
                    color: #C8A84B;
                }
                .wow-iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
            `;
            const style = document.createElement('style');
            style.innerHTML = css;
            document.head.appendChild(style);
        },

        createButton: function() {
            const btn = document.createElement('button');
            btn.className = 'wow-offerte-btn';
            btn.innerHTML = `<span>${this.config.buttonText}</span>`;
            btn.onclick = () => this.open();
            document.body.appendChild(btn);
        },

        createModal: function() {
            const overlay = document.createElement('div');
            overlay.className = 'wow-modal-overlay';
            overlay.id = 'wow-offerte-modal';
            
            overlay.onclick = (e) => {
                if (e.target === overlay) this.close();
            };

            const container = document.createElement('div');
            container.className = 'wow-modal-container';
            
            const close = document.createElement('div');
            close.className = 'wow-modal-close';
            close.innerHTML = '&times;';
            close.onclick = () => this.close();

            const iframe = document.createElement('iframe');
            iframe.className = 'wow-iframe';
            iframe.id = 'wow-offerte-iframe';

            container.appendChild(close);
            container.appendChild(iframe);
            overlay.appendChild(container);
            document.body.appendChild(overlay);

            // Listen for close signal from iframe
            window.addEventListener('message', (e) => {
                if (e.data === 'closeWizard') this.close();
            });
        },

        open: function() {
            const overlay = document.getElementById('wow-offerte-modal');
            const iframe = document.getElementById('wow-offerte-iframe');
            
            // Lazy load iframe source
            if (!iframe.src || iframe.src === 'about:blank') {
                iframe.src = this.config.apiUrl;
            }
            
            overlay.style.display = 'flex';
            setTimeout(() => overlay.classList.add('active'), 10);
            document.body.style.overflow = 'hidden'; // Prevent scroll
        },

        close: function() {
            const overlay = document.getElementById('wow-offerte-modal');
            overlay.classList.remove('active');
            setTimeout(() => {
                overlay.style.display = 'none';
                document.body.style.overflow = '';
            }, 300);
        }
    };

    window.WOWOfferte = WOWOfferte;
})();
