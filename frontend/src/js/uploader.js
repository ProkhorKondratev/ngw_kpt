import { modal, table } from "..";
import TrashIcon from "bootstrap-icons/icons/trash.svg";
import ArrowDownIcon from "bootstrap-icons/icons/arrow-down.svg";
import XMLIcon from "bootstrap-icons/icons/filetype-xml.svg";
import DirIcon from "bootstrap-icons/icons/folder.svg";

class UploadFile {
    constructor(file, parent = null) {
        this.parent = parent;
        this.file = file;
        this.name = file.name;
        this.size = this.measureSize(file.size);
        this.type = file.type;

        this._accepted = false;
        this._baseEl = undefined;
    }

    measureSize(size) {
        const units = ["B", "KB", "MB", "GB", "TB"];
        let unitIndex = 0;

        while (size >= 1024) {
            size /= 1024;
            unitIndex++;
        }

        return size.toFixed(2) + " " + units[unitIndex];
    }

    render() {
        this._baseEl = document.createElement("div");
        this._baseEl.className = "uploader__file";
        this._baseEl.innerHTML = `
            <div class="uploader__file-info">
                <p>${this.name}</p>
                <span>${this.size}</span>
            </div>
            <div class="uploader__file-actions">
                <div class="ms-form-check">
                    <div class="ms-form-check__body">
                        <input type="checkbox" id="accept" name="accept" class="ms-checkbox" ${
                            this._accepted ? "checked" : ""
                        }>
                        </input>
                    </div>
                </div>
                <button title="Удалить файл из списка">${TrashIcon}</button>
            </div>
        `;

        this.initListeners();
        return this._baseEl;
    }

    get accepted() {
        return this._accepted;
    }

    set accepted(value) {
        this._accepted = value;
        if (!this._baseEl) return;

        const checkbox = this._baseEl.querySelector("#accept");
        checkbox.checked = value;

        this.parent.renderInfo();
    }

    initListeners() {
        const checkbox = this._baseEl.querySelector("#accept");
        checkbox.onchange = () => (this.accepted = checkbox.checked);

        const deleteBtn = this._baseEl.querySelector("button");
        deleteBtn.onclick = () => this.remove();
    }

    remove() {
        this.parent.files = this.parent.files.filter((file) => file.name !== this.name);
        this.accepted = false;
        this._baseEl.remove();
    }
}

class UploadDirectory {
    constructor(directory, parent = null) {
        this.parent = parent;
        this.directory = directory;
        this.name = directory.name;
        this.path = directory.fullPath;
        this.files = [];

        this._baseEl = undefined;
    }

    render() {
        this._baseEl = document.createElement("div");
        this._baseEl.className = "uploader__directory";
        this._baseEl.innerHTML = `
            <div class="uploader__directory-header">
                <div class="uploader__directory-header__info">
                    <p>${this.name}</p>
                    <span>${this.path}</span>
                </div>
                <div class="uploader__directory-header__actions">
                    <button title="Удалить директорию вместе с файлами">${TrashIcon}</button>
                </div>
            </div>
            <div class="uploader__directory-files"></div>
        `;

        this.renderFiles();
        this.initListeners();
        return this._baseEl;
    }

    renderFiles() {
        const acceptedFilesEl = document.createElement("div");
        acceptedFilesEl.className = "accepted-files";

        const rejectedFilesEl = document.createElement("div");
        rejectedFilesEl.className = "rejected-files";
        rejectedFilesEl.innerHTML = `
            <div class="rejected-files__header" title="Блок непрошедших проверку файлов">
                <p>Непрошедшие проверку</p>
                <button>${ArrowDownIcon}</button>
            </div>
            <div class="rejected-files__body">
                <div class="rejected-files__body-files"></div>
            </div>
        `;
        const rejectedFiles = rejectedFilesEl.querySelector(".rejected-files__body-files");

        this.files.forEach((file) => {
            if (file.accepted) acceptedFilesEl.appendChild(file.render());
            else rejectedFiles.appendChild(file.render());
        });

        const dirFilesEl = this._baseEl.querySelector(".uploader__directory-files");

        const emptyMessage = document.createElement("p");
        emptyMessage.className = "empty-message";
        emptyMessage.textContent = "Файлы отсутствуют или не прошли проверку";

        if (acceptedFilesEl.children.length > 0) dirFilesEl.appendChild(acceptedFilesEl);
        if (rejectedFiles.children.length > 0) dirFilesEl.appendChild(rejectedFilesEl);
        if (dirFilesEl.children[0] !== acceptedFilesEl) dirFilesEl.prepend(emptyMessage);
    }

    initListeners() {
        const deleteBtn = this._baseEl.querySelector(".uploader__directory-header__actions button");
        deleteBtn.onclick = () => this.remove();

        const showBtn = this._baseEl.querySelector(".rejected-files__header");

        if (showBtn) {
            const body = this._baseEl.querySelector(".rejected-files__body");
            showBtn.onclick = () => {
                body.classList.toggle("show");
                modal.update();

                if (body.classList.contains("show")) showBtn.querySelector("svg").style.transform = "rotate(180deg)";
                else showBtn.querySelector("svg").style.transform = "rotate(0deg)";
            };
        }
    }

    remove() {
        this.parent.directories = this.parent.directories.filter((directory) => directory.name !== this.name);
        this.files.forEach((file) => file.remove());
        this._baseEl.remove();
    }

    renderInfo() {
        this.parent.renderInfo();
    }
}

export class UploadHandler {
    constructor() {
        this.files = [];
        this.directories = [];

        this._baseEl = undefined;
        this._dropZone = undefined;
    }

    init() {
        this.renderModal();
        this.initListeners();

        return this;
    }

    renderModal() {
        this._baseEl = document.createElement("div");
        this._baseEl.className = "uploader";
        this._baseEl.innerHTML = `
            <div class="uploader__dropzone">
                <div class="dropzone">
                    <div class="dropzone__title">
                        <p>Выберите или перетащите файлы в заданную область</p>
                        <span>Папки с архивами или ZIP-файлы с выписками</span>
                    </div>
                </div>
            </div>
            <div class="uploader__info"></div>
            <div class="uploader__files"></div>
            <div class="uploader__form"></div>
            <div class="uploader__footer"></div>
        `;

        this.renderForm();
        this.renderFooter();
        modal.setContent(this._baseEl);
    }

    renderForm() {
        const formEl = this._baseEl.querySelector(".uploader__form");
        formEl.innerHTML = `
            <form class="ms-form">
                <div class="ms-form-select">
                    <div class="ms-form-select__body">
                        <label class="ms-form-label" for="name">Название группы:</label>
                        <input class="ms-input" type="text" id="name" name="name">
                    </div>
                    <p class="ms-form-info">Имя группы, в которую будут добавлены файлы</p>
                </div>
                <div class="ms-form-check">
                    <div class="ms-form-check__body">
                        <label for="force_add">Принудительное добавление:</label>
                        <input type="checkbox" id="force_add" name="force_add" class="ms-checkbox">
                    </div>
                    <p class="ms-form-info">Добавить файлы, даже если они уже были обработаны ранее</p>
                </div>
                <div class="ms-form-select">
                    <div class="ms-form-select__body">
                        <label class="ms-form-label" for="format">Формат результатов:</label>
                        <select class="ms-input" id="format" name="format">
                            <option value="GeoJSON">GeoJSON</option>
                            <option value="MapInfo File">MapInfo Tab</option>
                            <option value="ESRI Shapefile" selected>ESRI ShapeFile</option>
                            <option value="GPKG">GeoPackage</option>
                        </select>
                    </div>
                    <p class="ms-form-info">Формат, в который будут конвертированы файлы</p>
                </div>
                <div class="ms-form-check">
                    <div class="ms-form-check__body">
                        <label for="merge_objects">Объединять объекты одного типа:</label>
                        <input type="checkbox" name="merge_objects" id="merge_objects" class="ms-checkbox">
                    </div>
                    <p class="ms-form-info">Если конвертируются несколько XML с объектами одного типа</p>
                </div>
                <div class="ms-form-check">
                    <div class="ms-form-check__body">
                        <label for="skip_empty_geom">Пропускать объекты без геометрии:</label>
                        <input type="checkbox" name="skip_empty_geom" id="skip_empty_geom" class="ms-checkbox">
                    </div>
                    <p class="ms-form-info">Игнорировать объекты без координат</p>
                </div>
                <div class="ms-form-check">
                    <div class="ms-form-check__body">
                        <label for="remove_empty_attrs">Удалять пустые атрибуты:</label>
                        <input type="checkbox" name="remove_empty_attrs" id="remove_empty_attrs" class="ms-checkbox">
                    </div>
                    <p class="ms-form-info">Целиком удалить колонку, если нет информации ни по одному объекту</p>
                </div>
                <div class="ms-form-check">
                    <div class="ms-form-check__body">
                        <label for="convert_additional_data">Конвертировать доп. данные (табличные):</label>
                        <input type="checkbox" name="convert_additional_data" id="convert_additional_data" class="ms-checkbox">
                    </div>
                    <p class="ms-form-info">Конвертировать информацию о правах собственности, сделках и т.д</p>
                </div>
            </form>
        `;
    }

    renderFooter() {
        const footerEl = this._baseEl.querySelector(".uploader__footer");
        footerEl.innerHTML = `
            <div class="modal-footer">
                <button class="ms-btn secondary" id="btn-cancel">Отмена</button>
                <button class="ms-btn success" id="btn-upload">Загрузить</button>
            </div>
        `;

        const cancelBtn = footerEl.querySelector("#btn-cancel");
        cancelBtn.onclick = () => modal.close();

        const uploadBtn = footerEl.querySelector("#btn-upload");
        uploadBtn.onclick = async () => {
            uploadBtn.disabled = true;
            await this.upload();
            uploadBtn.disabled = false;
        };
    }

    renderInfo() {
        const dirCount = this.directories.length;
        let acceptedFiles = 0;
        this.directories.forEach((dir) => {
            acceptedFiles += dir.files.filter((file) => file.accepted).length;
        });
        acceptedFiles += this.files.filter((file) => file.accepted).length;
        const infoEl = this._baseEl.querySelector(".uploader__info");
        infoEl.innerHTML = `
            <div class="uploader__info-item">
                ${DirIcon}
                <p>Обработано папок:</p>
                <span>${dirCount}</span>
            </div>
            <div class="uploader__info-item">
                ${XMLIcon}
                <p>Принято XML:</p>
                <span>${acceptedFiles}</span>
            </div>
        `;
    }

    initListeners() {
        const openBtn = document.querySelector(".kpt-stats__buttons button:nth-child(2)");
        openBtn.onclick = () => modal.open("Загрузка файлов");

        this._dropZone = this._baseEl.querySelector(".uploader__dropzone");
        this._dropZone.ondragenter = (e) => {
            e.preventDefault();
            this._dropZone.classList.add("hover");
        };

        this._dropZone.ondragover = (e) => {
            e.preventDefault();
            this._dropZone.classList.add("hover");
        };

        this._dropZone.ondragleave = (e) => {
            e.preventDefault();
            let relatedTarget = e.relatedTarget;
            if (!this._dropZone.contains(relatedTarget)) {
                this._dropZone.classList.remove("hover");
            }
        };

        this._dropZone.ondrop = async (e) => {
            e.preventDefault();
            this._dropZone.classList.remove("hover");

            const items = e.dataTransfer.items;
            await this.processItems(items);
        };

        this._dropZone.onclick = (e) => {
            const input = document.createElement("input");
            input.type = "file";
            input.multiple = true;
            input.accept = ".zip";
            input.click();

            input.onchange = async (e) => {
                e.preventDefault();
                await this.processItems(e.target.files);
            };
        };

        modal.onClose = () => this.clearFiles();
    }

    async processItems(items) {
        this._baseEl.classList.toggle("disabled");
        this.clearFiles();

        const promises = [];
        for (const item of items) {
            if (item instanceof DataTransferItem) {
                const entry = item.webkitGetAsEntry();
                if (entry) promises.push(this.processEntry(entry));
            } else if (item instanceof File) {
                const fileEntry = { isFile: true, file: item };
                promises.push(this.processEntry(fileEntry));
            }
        }
        await Promise.all(promises);

        if (this.files.length > 0) this.renderFiles();
        if (this.directories.length > 0) this.renderDirectories();
        this.renderInfo();

        this._baseEl.classList.toggle("disabled");
    }

    async processEntry(entry, parent = null) {
        if (entry.isFile) {
            const filePromise = new Promise((resolve) => {
                if (typeof entry.file === "function") {
                    entry.file((file) => {
                        resolve(new UploadFile(file));
                    });
                } else resolve(new UploadFile(entry.file));
            });

            const file = await filePromise;
            this.checkFile(file);

            if (parent) {
                file.parent = parent;
                parent.files.push(file);
            } else {
                file.parent = this;
                this.files.push(file);
            }
        } else if (entry.isDirectory) {
            const directory = new UploadDirectory(entry, this);

            const reader = entry.createReader();
            await new Promise((resolve) => {
                reader.readEntries(async (entries) => {
                    for (const entry of entries) {
                        await this.processEntry(entry, directory);
                    }
                    resolve();
                });
            });

            this.directories.push(directory);
        }
    }

    renderFiles() {
        const filesEl = this._baseEl.querySelector(".uploader__files");

        const files = new DocumentFragment();
        this.files.forEach((file) => {
            files.appendChild(file.render());
        });

        filesEl.appendChild(files);
        modal.update();
    }

    renderDirectories() {
        const directoryEl = this._baseEl.querySelector(".uploader__files");

        const directories = new DocumentFragment();
        this.directories.forEach((directory) => {
            directories.appendChild(directory.render());
        });

        directoryEl.appendChild(directories);
        modal.update();
    }

    checkFile(file) {
        if (file.file.size >= 50 * 1024 && file.file.name.toLowerCase().endsWith(".zip")) {
            file.accepted = true;
        }
    }

    collectFiles() {
        const files = this.files.filter((file) => file.accepted);
        this.directories.forEach((directory) => {
            files.push(...directory.files.filter((file) => file.accepted));
        });

        return files;
    }

    clearFiles() {
        this.files.forEach((file) => file.remove());
        this.directories.forEach((directory) => directory.remove());
    }

    async upload() {
        const files = this.collectFiles();
        if (files.length === 0) {
            UploadHandler.showAlert("Файлы не выбраны!", "warning");
            return;
        }

        const form = document.querySelector(".ms-form");
        const formData = new FormData(form);
        files.forEach((file) => formData.append("files", file.file));

        // for (let [name, value] of formData) {
        //     console.log(`${name} = ${value}`);
        // }

        const response = await fetch("/processing/run", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (!response.ok) {
            console.error(data.detail);

            if (Array.isArray(data.detail)) {
                const errors = data.detail
                    .map((error) => {
                        const location = error.loc.join(" > ");
                        return `${location}: ${error.msg}`;
                    })
                    .join("\n");

                UploadHandler.showAlert(errors, "danger");
            } else if (data.detail) UploadHandler.showAlert(data.detail, "danger");
            else UploadHandler.showAlert("Неизвестная ошибка", "danger");

            return;
        }

        UploadHandler.showAlert("Файлы успешно загружены", "success");
        modal.close();
        table.update();
    }

    static showAlert(message, type = "success") {
        const alert = document.createElement("div");
        alert.className = `kpt-badge alert ${type}`;
        alert.innerHTML = `${message}`;
        document.querySelector(".alert-wrapper").prepend(alert);

        alert.onanimationend = (e) => {
            if (e.animationName === "fadeOut") alert.remove();
        };
    }

    async makeRequest(url, method, body = null) {
        return await fetch(url, {
            method: method,
            body: body,
        })
            .then((response) => {
                if (!response.ok) throw new Error("Ошибка при выполнении запроса!");
                return response.json();
            })
            .then((data) => {
                UploadHandler.showAlert(data.message);
                return data;
            })
            .catch((error) => {
                UploadHandler.showAlert("Ошибка при выполнении запроса!", "danger");
                console.error(error);
            });
    }

    async deleteTask(id, element = null) {
        if (element) element.disabled = true;
        table.stopUpdate();

        await this.makeRequest(`/data/tasks/${id}`, "DELETE");
        table.update();

        if (element) element.disabled = false;
        table.startUpdate();
    }

    async deleteGroup(id, element = null) {
        if (element) element.disabled = true;
        table.stopUpdate();

        await this.makeRequest(`/data/groups/${id}`, "DELETE");
        table.update();

        if (element) element.disabled = false;
        table.startUpdate();
    }

    async restartTask(id, element = null) {
        if (element) element.disabled = true;
        table.stopUpdate();

        await this.makeRequest(`/processing/tasks/${id}/restart`, "GET");
        table.update();

        if (element) element.disabled = false;
        table.startUpdate();
    }

    async restartGroup(id, element = null) {
        if (element) element.disabled = true;
        table.stopUpdate();

        await this.makeRequest(`/processing/groups/${id}/restart`, "GET");
        table.update();

        if (element) element.disabled = false;
        table.startUpdate();
    }

    async downloadFile(type, id, name, element) {
        if (element) element.disabled = true;
        table.stopUpdate();

        try {
            const response = await fetch(`/data/${type}/${id}/download`);
            if (!response.ok) throw new Error("Ошибка при скачивании файла!");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = name + ".zip";
            a.click();

            window.URL.revokeObjectURL(url);
        } catch (error) {
            UploadHandler.showAlert("Ошибка при скачивании файла!", "danger");
            console.error(error);
        } finally {
            if (element) element.disabled = false;
            table.startUpdate();
        }
    }
}
