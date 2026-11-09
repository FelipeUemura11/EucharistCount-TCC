import { OctagonAlert } from "lucide-react";

export default function AvisoContagemDescartada() {
    return (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-5 py-3 text-sm font-semibold text-red-700">
            <OctagonAlert size={20} className="shrink-0" />
            Contagem não confiável nesta missa: confira a igreja para definir as hóstias.
        </div>
    );
}
