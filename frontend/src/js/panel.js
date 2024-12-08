import PauseBtn from "bootstrap-icons/icons/pause-fill.svg";
import PlayBtn from "bootstrap-icons/icons/play-fill.svg";
import { UploadHandler } from "./uploader.js";
import { table } from "..";

export class StatisticsPanel {
    constructor() {
        this.updateInterval = null;
    }

    init() {
        this.collectElements();
        this.startUpdate();
        this.initPauseButton();
        this.init_filter_buttons();

        return this;
    }

    collectElements() {
        const items = document.querySelectorAll(".kpt-stats__items span");

        this.loaded = items[0];
        this.working = items[1];
        this.success = items[2];
        this.error = items[3];
        this.remaining = items[4];
    }

    updateStatistics(loaded, working, success, error, remaining) {
        this.loaded.textContent = loaded;
        this.working.textContent = working;
        this.success.textContent = success;
        this.error.textContent = error;
        this.remaining.textContent = remaining;
    }

    async fetchStatistics() {
        try {
            const response = await fetch("/data/statistics");
            const data = await response.json();

            this.updateStatistics(data.loaded, data.in_progress, data.completed, data.failed, data.remaining);
        } catch (error) {
            console.error(error);
        }
    }

    startUpdate() {
        this.fetchStatistics();
        this.updateInterval = setInterval(() => {
            this.fetchStatistics();
        }, 8000);
    }

    stopUpdate() {
        clearInterval(this.updateInterval);
        this.updateInterval = null;
    }

    async initPauseButton() {
        const pauseBtn = document.querySelectorAll(".kpt-stats__buttons button")[0];

        const response = await fetch("/processing/status");
        if (response.ok) {
            const data = await response.json();
            pauseBtn.style.display = "block";

            if (data.status === "running") {
                pauseBtn.innerHTML = PauseBtn;
                pauseBtn.title = "Приостановить обработку";
            } else {
                pauseBtn.innerHTML = PlayBtn;
                pauseBtn.title = "Возобновить обработку";
                UploadHandler.showAlert("Обработка приостановлена", "warning");
            }

            pauseBtn.onclick = async () => {
                pauseBtn.disabled = true;
                const response = await fetch("/processing/toggle");
                if (response.ok) {
                    const data = await response.json();

                    if (data.status === "running") {
                        pauseBtn.innerHTML = PauseBtn;
                        pauseBtn.title = "Приостановить обработку";
                        UploadHandler.showAlert("Обработка возобновлена", "success");
                    } else {
                        pauseBtn.innerHTML = PlayBtn;
                        pauseBtn.title = "Возобновить обработку";
                        UploadHandler.showAlert("Обработка приостановлена", "warning");
                    }
                }
                pauseBtn.disabled = false;
            };
        }
    }

    init_filter_buttons() {
        const filterButtons = document.querySelectorAll(".kpt-stats__items .kpt-badge");

        filterButtons[0].onclick = () => {
            table.filter_by_status();
        };
        filterButtons[1].onclick = () => {
            table.filter_by_status(["parsing", "converting", "postprocessing"]);
        };
        filterButtons[2].onclick = () => {
            table.filter_by_status(["completed"]);
        };
        filterButtons[3].onclick = () => {
            table.filter_by_status(["failed"]);
        };
        filterButtons[4].onclick = () => {
            table.filter_by_status(["accepted", "parsing", "converting", "postprocessing"]);
        };
    }
}
