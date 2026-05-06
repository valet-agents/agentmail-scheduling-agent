<p align="center">
  <img src="https://agentmail.to/favicon.ico" alt="AgentMail" height="64" />
</p>

# AgentMail Scheduling Agent

A dedicated AgentMail inbox negotiates time with whoever emails it, follows your rules, and attaches an .ics calendar invite the moment a slot is confirmed. You stay CC'd. Slack is your console.

## Prerequisites
- An [AgentMail](https://agentmail.to) account (mint an API key in the dashboard)
- A Slack workspace where you can install the agent's bot and invite it to one channel
- The ability to subscribe an AgentMail webhook to a public URL (the agent's webhook URL is provisioned automatically — you'll paste it into one CLI command after deploy)

<table>
  <tr>
    <td><strong>CHANNELS</strong></td>
    <td><code>slack</code> · <code>webhook</code></td>
  </tr>
  <tr>
    <td><strong>CONNECTORS</strong></td>
    <td><code>agentmail</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <br />
      <a href="https://valet.dev/deploy?from=github.com/valet-agents/agentmail-scheduling-agent">
        <img src="https://raw.githubusercontent.com/valet-agents/agentmail-scheduling-agent/main/.github/deploy-button.svg" alt="Deploy Agent →" height="40" />
      </a>
      <br /><br />
    </td>
  </tr>
</table>

## How it works

1. AgentMail fires a webhook on every `message.received` event in the agent's dedicated inbox.
2. The agent reads the full thread, classifies the request (sales / internal / personal), and checks your rules.
3. It replies in-thread with three open slots that fit. You stay CC'd.
4. When the requester confirms a slot, the agent attaches an `.ics` calendar invite. Gmail, Outlook, and Apple Mail auto-detect it and surface a one-click "Add to calendar" for both attendees. No Google Calendar OAuth required.
5. Anytime, @mention the agent's Slack bot to ask what's pending, push a manual reply, or update your scheduling rules.

## Credits

Ported from the original [AgentMail Scheduling Agent](https://github.com/agentmail-to/agentmail-scheduling-agent) template by AgentMail. MIT-licensed.
