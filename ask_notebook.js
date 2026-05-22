#!/usr/bin/env node

/**
 * CLI Utility to manage and query your registered NotebookLM notebooks via the local MCP server.
 * Usage:
 *   note "your question"          - Ask a question to the active NotebookLM.
 *   note add <url> [name]         - Register a new notebook and set it as active.
 *   note list                     - List all registered notebooks.
 *   note use <id>                 - Set a notebook as active by ID.
 *   note remove <id>              - Remove a registered notebook.
 *   note info                     - Show status and which notebook is active.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const args = process.argv.slice(2);
const command = args[0] ? args[0].toLowerCase() : '';

const userHome = process.env.USERPROFILE || process.env.HOME || os.homedir();
const libraryPath = path.join(userHome, 'AppData', 'Local', 'notebooklm-mcp', 'Data', 'library.json');
const sessionFilePath = path.join(userHome, 'AppData', 'Local', 'notebooklm-mcp', 'Data', 'terminal_sessions.json');

function saveSessions(sessions) {
  try {
    const dir = path.dirname(sessionFilePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(sessionFilePath, JSON.stringify(sessions, null, 2));
  } catch (err) {}
}

function executeSelectNotebookMCP(notebookId, callback) {
  const mcp = spawn('npx', ['-y', 'notebooklm-mcp@latest'], { stdio: ['pipe', 'pipe', 'pipe'], shell: true });
  let stdoutBuffer = '';

  mcp.stdout.on('data', (data) => {
    stdoutBuffer += data.toString();
    if (stdoutBuffer.includes('"id":2') && stdoutBuffer.includes('"result"')) {
      mcp.kill();
      callback();
    }
  });

  setTimeout(() => {
    const initReq = {
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {},
        clientInfo: { name: "NotebookLM-MCP-CLI-Session-Initializer", version: "1.0.0" }
      }
    };
    mcp.stdin.write(JSON.stringify(initReq) + "\n");

    setTimeout(() => {
      const selectReq = {
        jsonrpc: "2.0",
        id: 2,
        method: "tools/call",
        params: {
          name: "select_notebook",
          arguments: { id: notebookId }
        }
      };
      mcp.stdin.write(JSON.stringify(selectReq) + "\n");
    }, 1000);
  }, 1000);
}

function registerNotebookViaMCP(url, name, callback) {
  let registeredId = '';

  const cmd1 = {
    jsonrpc: "2.0",
    id: 2,
    method: "tools/call",
    params: {
      name: "add_notebook",
      arguments: {
        url: url,
        name: name,
        description: "Registered via notebooklm-cli"
      }
    },
    handler: (msg) => {
      if (msg.error) {
        console.error(`❌ Error registering notebook: ${JSON.stringify(msg.error)}`);
        process.exit(1);
      }
      try {
        const textResult = msg.result.content[0].text;
        const res = JSON.parse(textResult);
        if (res.success && res.data && res.data.notebook) {
          registeredId = res.data.notebook.id;
          console.log(`✅ Notebook registered! Local ID: \x1b[32m${registeredId}\x1b[0m`);
        } else {
          console.log("Server response:", textResult);
        }
      } catch (e) {
        console.log("Raw output:", msg);
      }
    }
  };

  const cmd2 = () => {
    if (!registeredId) {
      console.log("⚠️  No ID to select. Exiting.");
      return null;
    }
    console.log(`🎯 Setting "${registeredId}" as the active default notebook...`);
    return {
      jsonrpc: "2.0",
      id: 3,
      method: "tools/call",
      params: {
        name: "select_notebook",
        arguments: { id: registeredId }
      },
      handler: (msg) => {
        if (msg.error) {
          console.error(`❌ Error selecting notebook: ${JSON.stringify(msg.error)}`);
          process.exit(1);
        } else {
          console.log(`\n🎉 \x1b[1m\x1b[32mSuccess!\x1b[0m Notebook \x1b[1m${registeredId}\x1b[0m is now active.`);

          const ppid = process.ppid;
          const todayStr = new Date().toISOString().split('T')[0];
          try {
            let sessions = {};
            if (fs.existsSync(sessionFilePath)) {
              sessions = JSON.parse(fs.readFileSync(sessionFilePath, 'utf8'));
            }
            sessions[`${ppid}`] = { notebookId: registeredId, date: todayStr };
            saveSessions(sessions);
          } catch (e) {}

          if (callback) {
            callback();
          } else {
            process.exit(0);
          }
        }
      }
    };
  };

  executeMCPCommands([cmd1, cmd2]);
}

function promptAndAddNotebook(callback) {
  const readline = require('readline');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  console.log('\n\x1b[1m\x1b[36m📝 Register New NotebookLM\x1b[0m');
  rl.question('🔗 Paste the NotebookLM URL from your browser:\n> ', (url) => {
    url = url.trim();
    if (!url) {
      console.error('❌ Error: URL cannot be empty.');
      rl.close();
      process.exit(1);
    }

    rl.question('\n🏷️  Give this notebook a name (e.g. my-project):\n> ', (customName) => {
      customName = customName.trim();
      rl.close();

      const notebookIdMatch = url.match(/\/notebook\/([a-zA-Z0-9\-]+)/);
      const derivedName = customName || (notebookIdMatch ? `Notebook ${notebookIdMatch[1].slice(0, 8)}` : 'New Notebook');

      console.log(`\n⚡ Registering notebook: "${derivedName}"...`);
      console.log(`🔗 URL: ${url}\n`);

      registerNotebookViaMCP(url, derivedName, callback);
    });
  });
}

function checkSessionNotebook(callback) {
  const isQuery = !['cadastrar', 'cadastar', 'add', 'listar', 'list', 'usar', 'use', 'select', 'remover', 'remove', 'status', 'info'].includes(command);

  if (!isQuery && args[0]) {
    return callback();
  }

  let library = null;
  try {
    if (fs.existsSync(libraryPath)) {
      library = JSON.parse(fs.readFileSync(libraryPath, 'utf8'));
    }
  } catch (err) {}

  if (!library || !library.notebooks || library.notebooks.length === 0) {
    return callback();
  }

  let sessions = {};
  try {
    if (fs.existsSync(sessionFilePath)) {
      sessions = JSON.parse(fs.readFileSync(sessionFilePath, 'utf8'));
    }
  } catch (err) {}

  const ppid = process.ppid;
  const todayStr = new Date().toISOString().split('T')[0];
  const sessionKey = `${ppid}`;
  const currentSession = sessions[sessionKey];

  if (currentSession && currentSession.date === todayStr && currentSession.notebookId) {
    if (library.active_notebook_id !== currentSession.notebookId) {
      console.log(`\x1b[90m[Session] Keeping notebook '${currentSession.notebookId}' active in this terminal.\x1b[0m`);
      executeSelectNotebookMCP(currentSession.notebookId, callback);
    } else {
      callback();
    }
    return;
  }

  const isInteractive = process.stdout.isTTY && process.stdin.isTTY;
  if (!isInteractive) {
    sessions[sessionKey] = { notebookId: library.active_notebook_id, date: todayStr };
    saveSessions(sessions);
    return callback();
  }

  console.log('\n\x1b[1m\x1b[36m🔔 New Terminal Session\x1b[0m');
  console.log('Select a notebook for this terminal session:');

  library.notebooks.forEach((nb, index) => {
    const isDefault = nb.id === library.active_notebook_id;
    const marker = isDefault ? ' \x1b[32m(active default)\x1b[0m' : '';
    const nameColor = isDefault ? '\x1b[1m\x1b[32m' : '';
    console.log(`  \x1b[1m${index + 1}\x1b[0m) ${nameColor}${nb.id}\x1b[0m - ${nb.name}${marker}`);
  });
  console.log(`  \x1b[1m${library.notebooks.length + 1}\x1b[0m) Register a new notebook`);

  const readline = require('readline');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  const defaultNotebookId = library.active_notebook_id;
  rl.question(`\nChoose (1-${library.notebooks.length + 1}) or press Enter for [${defaultNotebookId}]: `, (answer) => {
    rl.close();

    const choice = answer.trim();
    if (choice === '') {
      sessions[sessionKey] = { notebookId: defaultNotebookId, date: todayStr };
      saveSessions(sessions);
      console.log(`\n🎯 Using default: \x1b[1m\x1b[32m${defaultNotebookId}\x1b[0m\n`);
      callback();
    } else {
      const idx = parseInt(choice, 10) - 1;
      if (idx >= 0 && idx < library.notebooks.length) {
        const selectedId = library.notebooks[idx].id;
        sessions[sessionKey] = { notebookId: selectedId, date: todayStr };
        saveSessions(sessions);
        console.log(`\n🎯 Activating: \x1b[1m\x1b[32m${selectedId}\x1b[0m\n`);

        if (selectedId !== library.active_notebook_id) {
          executeSelectNotebookMCP(selectedId, callback);
        } else {
          callback();
        }
      } else if (idx === library.notebooks.length) {
        promptAndAddNotebook(callback);
      } else {
        console.log(`\n⚠️  Invalid option. Using default: \x1b[1m\x1b[32m${defaultNotebookId}\x1b[0m\n`);
        sessions[sessionKey] = { notebookId: defaultNotebookId, date: todayStr };
        saveSessions(sessions);
        callback();
      }
    }
  });
}

function printHelp() {
  console.log('\n📓 \x1b[1m\x1b[36mNotebookLM CLI\x1b[0m');
  console.log('─────────────────────────────────────────────────────────────────────');
  console.log('\x1b[1mUsage:\x1b[0m');
  console.log('  \x1b[32mnote "your question"\x1b[0m       Ask the active NotebookLM a question.');
  console.log('  \x1b[32mnote add <url> [name]\x1b[0m      Register a notebook from its share URL.');
  console.log('  \x1b[32mnote list\x1b[0m                  List all registered notebooks.');
  console.log('  \x1b[32mnote use <id>\x1b[0m              Set a notebook as active by ID.');
  console.log('  \x1b[32mnote remove <id>\x1b[0m           Remove a registered notebook.');
  console.log('  \x1b[32mnote info\x1b[0m                  Show server status and active notebook.');
  console.log('─────────────────────────────────────────────────────────────────────\n');
}

function executeMCPCommands(commandsList) {
  const mcp = spawn('npx', ['-y', 'notebooklm-mcp@latest'], { stdio: ['pipe', 'pipe', 'pipe'], shell: true });

  let currentCommandIndex = 0;
  let hasError = false;
  let initialized = false;
  let stdoutBuffer = '';
  const evaluatedCommands = [];

  function extractJSONRPCMessages(buffer) {
    const messages = [];
    let braceCount = 0;
    let inString = false;
    let escape = false;
    let startIndex = -1;

    for (let i = 0; i < buffer.length; i++) {
      const char = buffer[i];

      if (escape) { escape = false; continue; }
      if (char === '\\') { escape = true; continue; }
      if (char === '"') { inString = !inString; continue; }

      if (!inString) {
        if (char === '{') {
          if (braceCount === 0) startIndex = i;
          braceCount++;
        } else if (char === '}') {
          braceCount--;
          if (braceCount === 0 && startIndex !== -1) {
            messages.push({ text: buffer.slice(startIndex, i + 1), start: startIndex, end: i + 1 });
            startIndex = -1;
          }
        }
      }
    }
    return messages;
  }

  function sendNextCommand() {
    if (currentCommandIndex >= commandsList.length) {
      mcp.kill();
      process.exit(0);
    }

    const cmd = commandsList[currentCommandIndex];
    let reqObj;
    if (typeof cmd === 'function') {
      try {
        reqObj = cmd();
      } catch (err) {
        console.error(`❌ Error building request: ${err.message}`);
        mcp.kill();
        process.exit(1);
      }
    } else {
      reqObj = cmd;
    }

    evaluatedCommands[currentCommandIndex] = reqObj;

    if (reqObj) {
      mcp.stdin.write(JSON.stringify(reqObj) + "\n");
    } else {
      currentCommandIndex++;
      sendNextCommand();
    }
  }

  mcp.stdout.on('data', (data) => {
    stdoutBuffer += data.toString();

    while (true) {
      const parsedMsgs = extractJSONRPCMessages(stdoutBuffer);
      if (parsedMsgs.length === 0) break;

      const firstMsg = parsedMsgs[0];
      try {
        const msg = JSON.parse(firstMsg.text);
        stdoutBuffer = stdoutBuffer.slice(firstMsg.end);

        if (msg.id === 1 && msg.result && msg.result.protocolVersion) {
          initialized = true;
          sendNextCommand();
          continue;
        }

        const expectedId = currentCommandIndex + 2;
        if (initialized && msg.id === expectedId) {
          const cmd = evaluatedCommands[currentCommandIndex];
          const handler = cmd && cmd.handler;
          if (handler) handler(msg);

          currentCommandIndex++;
          sendNextCommand();
        }
      } catch (e) {
        stdoutBuffer = stdoutBuffer.slice(firstMsg.end);
      }
    }
  });

  mcp.stderr.on('data', (data) => {
    const errText = data.toString().trim();
    if (errText.includes('Opening page') || errText.includes('Sending query') || errText.includes('Scraping response') || errText.includes('cookies')) {
      console.log(`\x1b[90m[Status] ${errText.replace(/^.*\[\d{2}:\d{2}:\d{2}\]\s*/, '')}\x1b[0m`);
    }
  });

  mcp.on('close', (code) => {
    if (code !== 0 && !hasError && currentCommandIndex < commandsList.length) {
      console.log(`\nProcess finished with code ${code}.`);
    }
  });

  setTimeout(() => {
    mcp.stdin.write(JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {},
        clientInfo: { name: "NotebookLM-MCP-CLI", version: "1.0.0" }
      }
    }) + "\n");
  }, 2000);
}

// ─── Routing ──────────────────────────────────────────────────────────────────

if (!args[0]) {
  checkSessionNotebook(() => { printHelp(); process.exit(0); });
} else if (['ajuda', 'help', '-h', '--help'].includes(command)) {
  printHelp();
  process.exit(0);
} else if (['cadastrar', 'cadastar', 'add'].includes(command)) {
  const url = args[1];
  const customName = args.slice(2).join(' ');

  if (!url) {
    if (process.stdout.isTTY && process.stdin.isTTY) {
      promptAndAddNotebook();
    } else {
      console.error('\n❌ Error: Please provide the NotebookLM URL.\nUsage: note add <url> [name]\n');
      process.exit(1);
    }
  } else {
    const notebookIdMatch = url.match(/\/notebook\/([a-zA-Z0-9\-]+)/);
    const derivedName = customName || (notebookIdMatch ? `Notebook ${notebookIdMatch[1].slice(0, 8)}` : 'New Notebook');
    console.log(`\n⚡ Registering: "${derivedName}"...\n🔗 URL: ${url}\n`);
    registerNotebookViaMCP(url, derivedName);
  }
} else if (['listar', 'list'].includes(command)) {
  console.log('\n📚 Fetching registered notebooks...\n');

  let activeId = '';

  const cmd1 = {
    jsonrpc: "2.0", id: 2,
    method: "tools/call",
    params: { name: "get_library_stats", arguments: {} },
    handler: (msg) => {
      try {
        const res = JSON.parse(msg.result.content[0].text);
        activeId = (res.data || res).active_notebook;
      } catch (e) {}
    }
  };

  const cmd2 = {
    jsonrpc: "2.0", id: 3,
    method: "tools/call",
    params: { name: "list_notebooks", arguments: {} },
    handler: (msg) => {
      try {
        const res = JSON.parse(msg.result.content[0].text);
        const notebooks = res.data?.notebooks || [];

        if (notebooks.length === 0) {
          console.log("ℹ️  No notebooks registered yet.\n   Use: note add <url> [name]\n");
          return;
        }

        console.log('\x1b[1mRegistered Notebooks:\x1b[0m');
        console.log('─────────────────────────────────────────────────────────────────────');
        notebooks.forEach(nb => {
          const isActive = nb.id === activeId;
          const marker = isActive ? '\x1b[32m★ [ACTIVE]\x1b[0m' : '  [      ]';
          const nameColor = isActive ? '\x1b[1m\x1b[32m' : '\x1b[36m';
          console.log(`${marker} ID: ${nameColor}${nb.id}\x1b[0m`);
          console.log(`          Name: ${nb.name}`);
          console.log(`          URL:  ${nb.url}`);
          if (nb.description) console.log(`          Desc: ${nb.description}`);
          console.log('─────────────────────────────────────────────────────────────────────');
        });
        console.log(`\nSwitch active notebook: \x1b[36mnote use <id>\x1b[0m\n`);
      } catch (e) {
        console.error("Error parsing notebook list:", e);
      }
    }
  };

  executeMCPCommands([cmd1, cmd2]);
} else if (['usar', 'use', 'select'].includes(command)) {
  const selectId = args[1];
  if (!selectId) {
    console.error('\n❌ Error: Please provide the notebook ID.\nUsage: note use <id>\n');
    process.exit(1);
  }

  console.log(`\n🎯 Activating notebook: "${selectId}"...\n`);

  executeMCPCommands([{
    jsonrpc: "2.0", id: 2,
    method: "tools/call",
    params: { name: "select_notebook", arguments: { id: selectId } },
    handler: (msg) => {
      if (msg.error) {
        console.error(`❌ Error: ${JSON.stringify(msg.error)}`);
      } else {
        console.log(`🎉 \x1b[1m\x1b[32mSuccess!\x1b[0m Notebook \x1b[1m${selectId}\x1b[0m is now active.\nTry: \x1b[36mnote "your question"\x1b[0m\n`);
      }
    }
  }]);
} else if (['remover', 'remove'].includes(command)) {
  const removeId = args[1];
  if (!removeId) {
    console.error('\n❌ Error: Please provide the notebook ID.\nUsage: note remove <id>\n');
    process.exit(1);
  }

  console.log(`\n🗑️  Removing notebook "${removeId}"...\n`);

  executeMCPCommands([{
    jsonrpc: "2.0", id: 2,
    method: "tools/call",
    params: { name: "remove_notebook", arguments: { id: removeId } },
    handler: (msg) => {
      if (msg.error) {
        console.error(`❌ Error: ${JSON.stringify(msg.error)}`);
      } else {
        console.log(`🎉 \x1b[1m\x1b[32mSuccess!\x1b[0m Notebook \x1b[1m${removeId}\x1b[0m removed from local library.\n(Note: this does not delete the notebook on Google NotebookLM.)\n`);
      }
    }
  }]);
} else if (['status', 'info'].includes(command)) {
  console.log('\n📊 Fetching library status...\n');

  executeMCPCommands([{
    jsonrpc: "2.0", id: 2,
    method: "tools/call",
    params: { name: "get_library_stats", arguments: {} },
    handler: (msg) => {
      if (msg.error) {
        console.error(`❌ Error: ${JSON.stringify(msg.error)}`);
        return;
      }
      try {
        const res = JSON.parse(msg.result.content[0].text);
        const stats = res.data || res;
        console.log('\x1b[1mNotebookLM Integration Status:\x1b[0m');
        console.log('─────────────────────────────────────────────────────────────────────');
        console.log(`  Active Notebook:   \x1b[1m\x1b[32m${stats.active_notebook || 'None'}\x1b[0m`);
        console.log(`  Total Notebooks:   ${stats.total_notebooks || 0}`);
        console.log(`  Most Used:         ${stats.most_used_notebook || 'N/A'}`);
        console.log(`  Total Queries:     ${stats.total_queries || 0}`);
        console.log(`  Last Modified:     ${stats.last_modified ? new Date(stats.last_modified).toLocaleString() : 'N/A'}`);
        console.log('─────────────────────────────────────────────────────────────────────\n');
      } catch (e) {
        console.log("Raw response:", msg);
      }
    }
  }]);
} else {
  const query = args.join(' ');
  checkSessionNotebook(() => {
    console.log(`🔍 Querying NotebookLM: "${query}"...\n`);

    executeMCPCommands([{
      jsonrpc: "2.0", id: 2,
      method: "tools/call",
      params: { name: "ask_question", arguments: { question: query } },
      handler: (msg) => {
        if (msg.error) {
          console.error(`❌ Query error: ${JSON.stringify(msg.error)}`);
          return;
        }
        try {
          const textResult = msg.result.content[0].text;
          let answer = textResult;
          try {
            const parsed = JSON.parse(textResult);
            if (parsed?.text) answer = parsed.text;
            else if (parsed?.data?.answer) answer = parsed.data.answer;
          } catch (e) {}

          console.log('─────────────────────────────────────────────────────────────────────');
          console.log(answer);
          console.log('─────────────────────────────────────────────────────────────────────\n');
        } catch (e) {
          console.log("Raw output:\n", msg);
        }
      }
    }]);
  });
}
