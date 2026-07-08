<script lang="ts">
  import { formatCount, formatDateLabel, formatDurationMs } from "./lib/format";
  import type { ReviewStats } from "./lib/state";

  export let stats: ReviewStats;

  const supportingMetrics = [
    {
      label: "Reviewed cards",
      value: formatCount(stats.distinctCardCount),
      testId: "distinct-card-count"
    },
    {
      label: "Answers",
      value: formatCount(stats.reviewCount),
      testId: "review-count"
    },
    {
      label: "Total answer time",
      value: formatDurationMs(stats.totalAnswerTimeMs),
      testId: "total-answer-time"
    },
    {
      label: "Average per answer",
      value: formatDurationMs(stats.averagePerAnswerMs),
      testId: "average-per-answer"
    }
  ];
</script>

<main class="shell" aria-label="Average time per card today">
  <section class="summary">
    <div>
      <p class="eyebrow">{formatDateLabel(stats.dateLabel)}</p>
      <h1>Average time per card</h1>
    </div>
    <div class="primary-metric">
      <span class="primary-value" data-testid="average-per-card">
        {formatDurationMs(stats.averagePerCardMs)}
      </span>
      <span class="primary-label">per reviewed card today</span>
    </div>
  </section>

  <section class="metric-grid" aria-label="Supporting metrics">
    {#each supportingMetrics as metric (metric.testId)}
      <article class="metric">
        <span class="metric-label">{metric.label}</span>
        <span class="metric-value" data-testid={metric.testId}>{metric.value}</span>
      </article>
    {/each}
  </section>

  {#if stats.reviewCount === 0}
    <p class="empty" data-testid="empty-state">No reviews have been logged today.</p>
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    color: #172026;
    background: #f6f7f8;
    font-family:
      -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  :global(*) {
    box-sizing: border-box;
  }

  .shell {
    min-height: 100vh;
    padding: 24px;
  }

  .summary {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(220px, 320px);
    gap: 20px;
    align-items: end;
    padding: 28px;
    border: 1px solid #d8dde1;
    border-radius: 8px;
    background: #ffffff;
  }

  .eyebrow {
    margin: 0 0 8px;
    color: #4e6574;
    font-size: 13px;
    font-weight: 650;
  }

  h1 {
    margin: 0;
    font-size: 28px;
    font-weight: 720;
    letter-spacing: 0;
  }

  .primary-metric {
    display: flex;
    min-width: 0;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }

  .primary-value {
    max-width: 100%;
    color: #0f6b63;
    font-size: 42px;
    font-weight: 760;
    line-height: 1;
    overflow-wrap: anywhere;
  }

  .primary-label {
    color: #51606a;
    font-size: 14px;
    text-align: right;
  }

  .metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-top: 16px;
  }

  .metric {
    display: grid;
    gap: 8px;
    min-height: 92px;
    padding: 16px;
    border: 1px solid #d8dde1;
    border-radius: 8px;
    background: #ffffff;
  }

  .metric-label {
    color: #51606a;
    font-size: 13px;
  }

  .metric-value {
    align-self: end;
    color: #1d2a31;
    font-size: 24px;
    font-weight: 700;
    overflow-wrap: anywhere;
  }

  .empty {
    margin: 18px 0 0;
    padding: 14px 16px;
    border: 1px solid #d8dde1;
    border-radius: 8px;
    background: #ffffff;
    color: #51606a;
  }

  @media (max-width: 680px) {
    .shell {
      padding: 16px;
    }

    .summary {
      grid-template-columns: 1fr;
      padding: 20px;
    }

    .primary-metric {
      align-items: flex-start;
    }

    .primary-label {
      text-align: left;
    }

    .metric-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>
