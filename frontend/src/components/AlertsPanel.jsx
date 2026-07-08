import React from "react";
import { SEVERITY_STYLES, fmtMoney, fmtTime, shortId } from "@/lib/format";
import { DASHBOARD } from "@/constants/testIds";
import { ShieldAlert, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AlertsPanel({ items, onAck, user }) {
  const canAck = user?.role === "admin" || user?.role === "analyst";
  return (
    <div
      className="card-surface flex flex-col h-full"
      data-testid={DASHBOARD.alertStream}
    >
      <div className="flex items-center justify-between px-4 sm:px-5 py-3 border-b border-[#222630]">
        <div className="flex items-center gap-3">
          <div className="text-xs uppercase tracking-[0.2em] font-semibold text-[#F8FAFC]">
            Fraud Alerts
          </div>
          <span className="chip text-[#FF3366] bg-[#FF3366]/10 border-[#FF3366]/30">
            <ShieldAlert size={10} />
            alerts.raised
          </span>
        </div>
        <div className="text-[10px] font-mono text-[#64748B]">
          {items.length} active
        </div>
      </div>
      <div className="overflow-auto max-h-[560px] divide-y divide-[#181C24]">
        {items.length === 0 && (
          <div className="px-4 py-14 text-center text-[#64748B] text-xs font-mono">
            ~ no fraud alerts yet — inject a fraud tx to see one ~
          </div>
        )}
        {items.map((a) => {
          const sev = SEVERITY_STYLES[a.severity] || SEVERITY_STYLES.medium;
          return (
            <div
              key={a.alert_id}
              data-testid={DASHBOARD.alertRow(a.alert_id)}
              className={`px-4 py-3 flex flex-col gap-2 ${
                a.acknowledged ? "opacity-40" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`chip ${sev}`}>{a.severity}</span>
                  <span className="font-mono text-[11px] text-[#94A3B8]">
                    {fmtTime(a.raised_at)}
                  </span>
                </div>
                <div className="font-mono text-[11px] text-[#F8FAFC]">
                  score {a.fraud_score.toFixed(3)}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <div className="font-mono text-[13px] text-[#F8FAFC]">
                    {fmtMoney(a.amount)}{" "}
                    <span className="text-[#64748B]">·</span>{" "}
                    <span className="text-[#94A3B8]">
                      {a.merchant_category}
                    </span>{" "}
                    <span className="text-[#64748B]">·</span>{" "}
                    <span className="text-[#94A3B8]">{a.country}</span>
                  </div>
                  <div className="font-mono text-[10px] text-[#64748B]">
                    {a.user_id} · {shortId(a.tx_id, 10)}
                  </div>
                </div>
                {!a.acknowledged && canAck && (
                  <Button
                    variant="outline"
                    size="sm"
                    data-testid={DASHBOARD.btnAckAlert(a.alert_id)}
                    onClick={() => onAck && onAck(a.alert_id)}
                    className="h-7 border-[#333A4A] bg-transparent text-[#94A3B8] hover:text-[#00FF66] hover:border-[#00FF66]/50 hover:bg-[#00FF66]/5 font-mono text-[10px] uppercase tracking-wider"
                  >
                    <Check size={12} className="mr-1" />
                    ack
                  </Button>
                )}
              </div>
              <div className="flex flex-wrap gap-1">
                {(a.reasons || []).map((r) => (
                  <span
                    key={r}
                    className="chip text-[#FFB000] bg-[#FFB000]/5 border-[#FFB000]/20"
                  >
                    {r}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
