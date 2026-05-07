import http from "../server/axios";
import {
  USER_LOGIN,
  PRISON_LIST,
  PRISONER_LIST,
  PRISONER_DETAIL,
  PRISONER_EXIT_RECORD,
  EXIT_STATISTICS,
  REALTIME_STATISTICS,
  WORK_STATISTICS,
  MESSAGE_LIST,
  ACCOUNT_LIST,
  RESET_PASSWORD,
  PRISONER_ARCHIVE,
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
  list: (data) => http.get(PRISONER_EXIT_RECORD, data).then((res) => res?.data),
};

export const exitStatistics = {
  list: (data) => http.get(EXIT_STATISTICS, data).then((res) => res?.data),
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
  resetPwd: (data) => http.post(RESET_PASSWORD, data),
};

export const prisonerArchive = {
  list: (data) => http.get(PRISONER_ARCHIVE, data).then((res) => res?.data),
};
