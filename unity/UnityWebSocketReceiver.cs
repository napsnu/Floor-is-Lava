using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Threading;
using System.Threading.Tasks;
using WebSocketSharp;

public class UnityWebSocketReceiver : MonoBehaviour
{
    [SerializeField] private string serverUrl = "ws://localhost:8765";

    private WebSocket ws;
    private readonly Queue<string> messageQueue = new Queue<string>();
    private readonly object queueLock = new object();

    void Start()
    {
        Connect();
    }

    void OnDestroy()
    {
        if (ws != null)
        {
            ws.Close();
            ws = null;
        }
    }

    public void Connect()
    {
        ws = new WebSocket(serverUrl);
        ws.OnOpen += (sender, e) => { Debug.Log("[WS] Connected"); };
        ws.OnClose += (sender, e) => { Debug.Log("[WS] Closed"); };
        ws.OnError += (sender, e) => { Debug.LogError($"[WS] Error: {e.Message}"); };
        ws.OnMessage += (sender, e) =>
        {
            lock (queueLock)
            {
                messageQueue.Enqueue(e.Data);
            }
        };
        ws.ConnectAsync();
    }

    void Update()
    {
        // Pump queued messages to main thread
        while (true)
        {
            string msg = null;
            lock (queueLock)
            {
                if (messageQueue.Count > 0)
                {
                    msg = messageQueue.Dequeue();
                }
            }
            if (msg == null) break;
            HandleMessage(msg);
        }
    }

    private void HandleMessage(string json)
    {
        // For now, just log.
        Debug.Log($"[WS] Message: {json}");
        // TODO: Parse JSON and drive gameplay. Messages follow protocol in protocol.md
    }

    public void SendTileUpdate(List<Vector2Int> tiles)
    {
        if (ws == null || ws.ReadyState != WebSocketState.Open) return;
        var list = new List<int[]>();
        foreach (var t in tiles) list.Add(new int[] { t.x, t.y });
        var payload = new
        {
            type = "tile_update",
            lava_tiles = list
        };
        string json = JsonUtility.ToJson(new Wrapper(payload));
        ws.Send(json);
    }

    // Unity's JsonUtility doesn't handle anonymous types, so we wrap
    [Serializable]
    private class Wrapper
    {
        public string type;
        public List<IntArray> lava_tiles;
        public Wrapper(object payload)
        {
            var p = (dynamic)payload;
            type = p.type;
            lava_tiles = new List<IntArray>();
            foreach (var t in p.lava_tiles)
            {
                lava_tiles.Add(new IntArray { x = t[0], y = t[1] });
            }
        }
    }

    [Serializable]
    private class IntArray
    {
        public int x;
        public int y;
    }
} 