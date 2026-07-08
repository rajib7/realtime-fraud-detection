import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { DASHBOARD } from "@/constants/testIds";
import { Play, Square, Zap, SendHorizontal } from "lucide-react";
import { toast } from "sonner";
import {
  startSimulator,
  stopSimulator,
  configureSimulator,
  injectFraud,
  scoreTransaction,
} from "@/lib/api";
import { api } from "@/lib/api";

const MERCHANT_OPTIONS = [
  "grocery",
  "restaurant",
  "gas_station",
  "streaming",
  "electronics",
  "crypto_exchange",
  "wire_transfer",
  "gift_cards",
  "gambling",
];

const COUNTRY_OPTIONS = ["US", "GB", "DE", "IN", "SG", "BR", "NG", "RU"];

export default function DemoControls({ status, onChange, user: authUser }) {
  const [tps, setTps] = useState([status?.tps || 3]);
  const [bias, setBias] = useState([(status?.fraud_bias || 0.08) * 100]);
  const [busy, setBusy] = useState(false);
  const isAdmin = authUser?.role === "admin";

  const [user, setUser] = useState("user_9999");
  const [amount, setAmount] = useState("120");
  const [merchant, setMerchant] = useState("grocery");
  const [country, setCountry] = useState("US");
  const [scoring, setScoring] = useState(false);

  async function handleStart() {
    setBusy(true);
    try {
      await startSimulator({ tps: tps[0], fraud_bias: bias[0] / 100 });
      toast.success(`Simulator started at ${tps[0].toFixed(1)} TPS`);
      onChange && onChange();
    } finally {
      setBusy(false);
    }
  }

  async function handleStop() {
    setBusy(true);
    try {
      await stopSimulator();
      toast("Simulator stopped");
      onChange && onChange();
    } finally {
      setBusy(false);
    }
  }

  async function handleConfig() {
    await configureSimulator({ tps: tps[0], fraud_bias: bias[0] / 100 });
    onChange && onChange();
  }

  async function handleInject() {
    setBusy(true);
    try {
      const res = await injectFraud(3);
      toast.error(`Injected ${res.injected.length} fraud transactions`);
    } finally {
      setBusy(false);
    }
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    setScoring(true);
    try {
      const payload = {
        user_id: user || "user_9999",
        amount: parseFloat(amount) || 1,
        currency: "USD",
        merchant: `m_manual`,
        merchant_category: merchant,
        country,
        is_foreign: country !== "US",
        cross_border: country !== "US",
      };
      const { data } = await api.post("/tx/transactions", payload);
      toast.success(`tx submitted → ${data.tx_id.slice(0, 12)}`);
    } catch (err) {
      toast.error("submit failed");
    } finally {
      setScoring(false);
    }
  }

  const running = !!status?.running;

  return (
    <div className="card-surface p-4 sm:p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] font-semibold text-[#F8FAFC]">
            Demo Controls
          </div>
          <div className="text-[11px] font-mono text-[#64748B]">
            traffic simulator · fraud injection · manual tx
          </div>
        </div>
        <span
          data-testid={DASHBOARD.statusRunning}
          className={`chip ${
            running
              ? "text-[#00FF66] bg-[#00FF66]/10 border-[#00FF66]/40"
              : "text-[#64748B] bg-[#64748B]/10 border-[#64748B]/30"
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              running ? "bg-[#00FF66] live-dot" : "bg-[#64748B]"
            }`}
          />
          {running ? "RUNNING" : "IDLE"}
        </span>
      </div>

      <div className="flex gap-2">
        {!running ? (
          <Button
            data-testid={DASHBOARD.btnStart}
            disabled={busy || !isAdmin}
            onClick={handleStart}
            className="flex-1 bg-[#00E5FF] hover:bg-[#00E5FF]/90 text-[#0A0C10] font-mono uppercase tracking-wider text-xs h-9 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Play size={14} className="mr-2" />
            start stream
          </Button>
        ) : (
          <Button
            data-testid={DASHBOARD.btnStop}
            disabled={busy || !isAdmin}
            onClick={handleStop}
            variant="outline"
            className="flex-1 border-[#333A4A] bg-transparent text-[#F8FAFC] hover:bg-[#181C24] font-mono uppercase tracking-wider text-xs h-9 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Square size={12} className="mr-2" />
            stop
          </Button>
        )}
        <Button
          data-testid={DASHBOARD.btnInjectFraud}
          onClick={handleInject}
          disabled={busy || !isAdmin}
          className="bg-[#FF3366] hover:bg-[#FF3366]/90 text-[#0A0C10] font-mono uppercase tracking-wider text-xs h-9 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Zap size={14} className="mr-2" />
          inject fraud x3
        </Button>
      </div>

      {!isAdmin && (
        <div
          data-testid="rbac-admin-notice"
          className="text-[10.5px] font-mono text-[#FFB000] bg-[#FFB000]/8 border border-[#FFB000]/25 rounded px-2 py-1.5"
        >
          simulator controls & fraud injection require the{" "}
          <span className="font-semibold">admin</span> role.
        </div>
      )}

      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label className="text-[11px] uppercase tracking-[0.18em] text-[#94A3B8] font-semibold">
              throughput
            </Label>
            <span className="font-mono text-xs text-[#00E5FF]">
              {tps[0].toFixed(1)} tx/s
            </span>
          </div>
          <Slider
            data-testid={DASHBOARD.sliderTps}
            min={0.5}
            max={20}
            step={0.5}
            value={tps}
            onValueChange={setTps}
            onValueCommit={handleConfig}
            disabled={!isAdmin}
          />
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label className="text-[11px] uppercase tracking-[0.18em] text-[#94A3B8] font-semibold">
              fraud bias
            </Label>
            <span className="font-mono text-xs text-[#FFB000]">
              {bias[0].toFixed(0)}%
            </span>
          </div>
          <Slider
            data-testid={DASHBOARD.sliderFraudBias}
            min={0}
            max={60}
            step={1}
            value={bias}
            onValueChange={setBias}
            onValueCommit={handleConfig}
            disabled={!isAdmin}
          />
        </div>
      </div>

      <Separator className="bg-[#222630]" />

      <form onSubmit={handleManualSubmit} className="space-y-3">
        <div className="text-[11px] uppercase tracking-[0.18em] text-[#94A3B8] font-semibold">
          manual transaction
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label className="text-[10px] text-[#64748B] font-mono">user</Label>
            <Input
              data-testid={DASHBOARD.inputManualUser}
              value={user}
              onChange={(e) => setUser(e.target.value)}
              className="h-8 bg-[#0A0C10] border-[#222630] font-mono text-xs"
            />
          </div>
          <div>
            <Label className="text-[10px] text-[#64748B] font-mono">
              amount
            </Label>
            <Input
              data-testid={DASHBOARD.inputManualAmount}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              type="number"
              className="h-8 bg-[#0A0C10] border-[#222630] font-mono text-xs"
            />
          </div>
          <div>
            <Label className="text-[10px] text-[#64748B] font-mono">
              merchant category
            </Label>
            <Select value={merchant} onValueChange={setMerchant}>
              <SelectTrigger
                data-testid={DASHBOARD.selectManualMerchant}
                className="h-8 bg-[#0A0C10] border-[#222630] font-mono text-xs"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#11141A] border-[#222630] text-[#F8FAFC]">
                {MERCHANT_OPTIONS.map((m) => (
                  <SelectItem
                    key={m}
                    value={m}
                    className="font-mono text-xs focus:bg-[#181C24]"
                  >
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-[10px] text-[#64748B] font-mono">
              country
            </Label>
            <Select value={country} onValueChange={setCountry}>
              <SelectTrigger
                data-testid={DASHBOARD.selectManualCountry}
                className="h-8 bg-[#0A0C10] border-[#222630] font-mono text-xs"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#11141A] border-[#222630] text-[#F8FAFC]">
                {COUNTRY_OPTIONS.map((c) => (
                  <SelectItem
                    key={c}
                    value={c}
                    className="font-mono text-xs focus:bg-[#181C24]"
                  >
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button
          data-testid={DASHBOARD.btnManualSubmit}
          type="submit"
          disabled={scoring}
          variant="outline"
          className="w-full border-[#333A4A] bg-transparent hover:bg-[#181C24] text-[#F8FAFC] font-mono uppercase tracking-wider text-xs h-9"
        >
          <SendHorizontal size={12} className="mr-2" />
          submit tx
        </Button>
      </form>
    </div>
  );
}
