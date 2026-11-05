import { TriangleAlert } from "lucide-react";

interface AvisoContagemBaixaProps {
    habitual: number;
}

export default function AvisoContagemBaixa({ habitual }: AvisoContagemBaixaProps) {
    return (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-amber-800">
            <TriangleAlert size={22} className="mt-0.5 shrink-0" />
            <p className="m-0 text-sm">
                <strong>Contagem abaixo do habitual</strong> para este horário (normalmente cerca de {habitual} pessoas).
                A câmera pode ter perdido gente na entrada: confira a igreja e, se precisar, separe mais hóstias.
            </p>
        </div>
    );
}
