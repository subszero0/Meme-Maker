import { Suspense } from "react";
import TrimPageContent from "./TrimPageContent";

export default function TrimPage() {
  return (
    <Suspense fallback={<div>Loading trim page...</div>}>
      <TrimPageContent />
    </Suspense>
  );
}
