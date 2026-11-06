import { TriangleAlert } from "lucide-react";

export default function AvisoContagemBaixa() {
    return (
        <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-5 py-3 text-sm font-semibold text-amber-800">
            <TriangleAlert size={20} className="shrink-0" />
            Possível subcontagem
        </div>
    );
}
