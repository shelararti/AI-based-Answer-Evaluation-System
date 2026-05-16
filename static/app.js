document.addEventListener("DOMContentLoaded", () => {

    const runBtn = document.getElementById("runBtn");

    const questionEl = document.getElementById("question");
    const referenceEl = document.getElementById("reference");
    const studentEl = document.getElementById("student");
    const marksEl = document.getElementById("marks");

    const resultDiv = document.getElementById("result");
    const auditDiv = document.getElementById("audit");

    runBtn.addEventListener("click", async () => {

        const payload = {
            question: questionEl.value,
            reference: referenceEl.value,
            student: studentEl.value,
            max_marks: parseFloat(marksEl.value)
        };

        console.log("INPUT:", payload);

        try {
            const response = await fetch("/evaluate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            console.log("OUTPUT:", data);

            if (!data || !data.rubric) {
                resultDiv.innerHTML = `<p>Invalid response from server</p>`;
                auditDiv.innerHTML = "";
                return;
            }

            const rubric = data.rubric;

            // -----------------------------
            // RESULT (VERDICT CARD)
            // -----------------------------
            resultDiv.innerHTML = `
                <div class="verdict">
                    <div class="label">Final Score</div>
                    <h3>${data.score} / ${data.max_marks}</h3>

                    <div class="feedback">
                        ${data.feedback}
                    </div>
                </div>
            `;

            // -----------------------------
            // AUDIT (RUBRIC DASHBOARD)
            // -----------------------------
            auditDiv.innerHTML = Object.entries(rubric).map(([key, value]) => {

                const percent = Math.round(value * 100);

                return `
                    <div class="rubric-item">
                        <div class="rubric-top">
                            <span>${key.replaceAll("_", " ")}</span>
                            <span>${percent}%</span>
                        </div>

                        <div class="bar">
                            <div class="bar-fill" style="width:${percent}%"></div>
                        </div>
                    </div>
                `;
            }).join("");

        } catch (err) {
            console.error(err);

            resultDiv.innerHTML = `<p>Server error occurred</p>`;
            auditDiv.innerHTML = "";
        }
    });
});