import http from "../server/axios";
import {
  USER_LOGIN,
  PRISON_LIST,
  PRISONER_LIST,
  PRISONER_DETAIL,
  EXIT_RECORD,
  ENTRY_RECORD,
  RECORD_LIST,
  RECORD_EXPORT,
  REALTIME_STATISTICS,
  WORK_STATISTICS,
  MESSAGE_LIST,
  ACCOUNT_LIST,
  ACCOUNT_ADD,
  ACCOUNT_UPDATE,
  ACCOUNT_DELETE,
  RESET_PASSWORD,
  PRISONER_ARCHIVE,
  PRISON_MESSAGES,
  EXIT_TYPE_LIST,
  EXIT_TYPE_ADD,
  EXIT_TYPE_UPDATE,
  EXIT_TYPE_DELETE,
  RETURN_RECORD,
  VIDEO_STREAM_URL,
  CAMERA_LIST,
} from "./apis";

export const userLogin = (data) => http.post(USER_LOGIN, data);

export const prison = {
  list: (data) => http.get(PRISON_LIST, data).then((res) => res?.data),
};

export const prisoner = {
  list: (data) => http.get(PRISONER_LIST, data).then((res) => res?.data),
  detail: (data) => http.get(PRISONER_DETAIL, data),
};

export const exitRecord = {
  submit: (data) => http.post(EXIT_RECORD, data),
};

export const entryRecord = {
  submit: (data) => http.post(ENTRY_RECORD, data),
};

export const returnRecord = {
  submit: (data) => http.post(RETURN_RECORD, data),
};

export const record = {
  list: (data) => http.get(RECORD_LIST, data).then((res) => res?.data),
};

export const recordExport = {
  get: (data) => http.get(RECORD_EXPORT, data).then((res) => res?.data),
};

export const realtimeStatistics = {
  get: (data) => http.get(REALTIME_STATISTICS, data).then((res) => res?.data),
};

export const workStatistics = {
  list: (data) => http.get(WORK_STATISTICS, data).then((res) => res?.data),
};

export const message = {
  list: (data) => http.get(MESSAGE_LIST, data).then((res) => res?.data),
};

export const account = {
  list: (data) => http.get(ACCOUNT_LIST, data).then((res) => res?.data),
  add: (data) => http.post(ACCOUNT_ADD, data),
  update: (data) => http.post(ACCOUNT_UPDATE, data),
  delete: (data) => http.post(ACCOUNT_DELETE, data),
  resetPwd: (data) => http.post(RESET_PASSWORD, data),
};

export const prisonerArchive = {
  list: (data) => http.get(PRISONER_ARCHIVE, data).then((res) => res?.data),
};

export const exitType = {
  list: (data) => http.get(EXIT_TYPE_LIST, data).then((res) => res?.data),
  add: (data) => http.post(EXIT_TYPE_ADD, data),
  update: (data) => http.post(EXIT_TYPE_UPDATE, data),
  delete: (data) => http.post(EXIT_TYPE_DELETE, data),
};

export const prisonMessages = {
  list: (data) => http.get(PRISON_MESSAGES, data).then((res) => res?.data),
};

export const video = {
  getStreamUrl: (data, timeout) => http.get(VIDEO_STREAM_URL, data, timeout).then((res) => res?.data),
  getCameraList: (data) => http.get(CAMERA_LIST, data).then((res) => res?.data),
};
