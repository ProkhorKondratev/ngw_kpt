export class DynamicModal {
    constructor(container = document.body) {
        this.container = container;
        this.modal = null;
        this.modalContent = null;

        this.onClose = null;
        this.onOpen = null;

        this.init();
    }

    init() {
        this.render();
        this.initListeners();
    }

    render() {
        this.modal = document.createElement("div");
        this.modal.className = "ms-modal";

        this.modalContent = document.createElement("div");
        this.modalContent.className = "ms-modal-content";
        this.modalContent.innerHTML = `
            <div class="ms-modal__header">
                <span class="ms-modal-title"></span>
                <button class="ms-modal-close">
                    <p>✕</p>
                </button>
            </div>
            <div class="ms-modal-body"></div>
        `;

        this.modal.appendChild(this.modalContent);
        this.container.appendChild(this.modal);
    }

    open(title = null, content = null) {
        if (title) this.modalContent.querySelector(".ms-modal-title").textContent = title;
        if (content) this.setContent(content);
        if (this.onOpen) this.onOpen();
        this.modal.classList.add("show");
        this.modalContent.classList.add("show");
    }

    close() {
        this.modal.classList.remove("show");
        this.modalContent.classList.remove("show");
        setTimeout(() => {
            if (this.onClose) this.onClose();
        }, 500);
    }

    setContent(content, place = ".ms-modal-body") {
        const body = this.modalContent.querySelector(place);
        if (typeof content === "string") body.innerHTML = content;
        else {
            body.innerHTML = "";
            body.appendChild(content);
        }
        this.update();
    }

    initListeners() {
        const closeButton = this.modalContent.querySelector(".ms-modal-close");
        closeButton.onclick = () => this.close();

        this.modal.onmousedown = (e) => {
            if (e.target === this.modal) this.close();
        };
    }

    update() {
        if (this.modalContent.scrollHeight > window.innerHeight * 0.8) {
            this.modalContent.style.maxHeight = `${window.innerHeight * 0.8}px`;
            this.modalContent.style.overflowY = "auto";
        } else {
            this.modalContent.style.maxHeight = `${this.modalContent.scrollHeight}px`;
            this.modalContent.style.overflowY = "hidden";
        }
    }
}
