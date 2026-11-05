import { TriangleAlert } from "lucide-react";

interface AvisoContagemBaixaProps {
    habitual: number;
}

export default function AvisoContagemBaixa({ habitual }: AvisoContagemBaixaProps) {
    return (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-amber-800">
            <TriangleAlert size={22} className="mt-0.5 shrink-0" />
            <p className="m-0 text-sm">
                <strong>Hoje há menos gente que o normal</strong> nesta missa (costuma ter cerca de {habitual} pessoas).
                Vale conferir a igreja e, se estiver mais cheia, separar mais hóstias.
            </p>
        </div>
    );
}
