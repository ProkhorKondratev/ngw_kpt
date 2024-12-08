import { KptTable } from "./js/table.js";
import { DynamicModal } from "./dynamic_modal";
import { StatisticsPanel } from "./js/panel.js";
import { UploadHandler } from "./js/uploader.js";
import "datatables.net-dt/css/dataTables.dataTables.min.css";
import "./css/styles.scss";
import "./dynamic_modal/styles.scss";

export const modal = new DynamicModal();
export const panel = new StatisticsPanel().init();
export const table = new KptTable().init();
export const uploader = new UploadHandler().init();
