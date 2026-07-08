export const DASHBOARD = {
  // header/nav
  header: "dashboard-header",
  tabDashboard: "tab-dashboard",
  tabArchitecture: "tab-architecture",
  tabApi: "tab-api-explorer",
  tabNotes: "tab-design-notes",

  // controls
  btnStart: "btn-start-simulator",
  btnStop: "btn-stop-simulator",
  btnInjectFraud: "btn-inject-fraud",
  sliderTps: "slider-tps",
  sliderFraudBias: "slider-fraud-bias",

  // manual tx form
  inputManualUser: "input-manual-user",
  inputManualAmount: "input-manual-amount",
  selectManualMerchant: "select-manual-merchant",
  selectManualCountry: "select-manual-country",
  btnManualSubmit: "btn-manual-submit",

  // kpi cards
  kpiTps: "kpi-tps",
  kpiLatency: "kpi-latency",
  kpiFraudRate: "kpi-fraud-rate",
  kpiAlerts: "kpi-alerts",

  // streams
  txStream: "tx-stream",
  txRow: (id) => `tx-row-${id}`,
  alertStream: "alert-stream",
  alertRow: (id) => `alert-row-${id}`,
  btnAckAlert: (id) => `btn-ack-alert-${id}`,

  // status pills
  statusRunning: "status-simulator-running",
};
