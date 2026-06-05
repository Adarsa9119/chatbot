import ChatWindow from '../components/ChatWindow';

export default function ChatPage() {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <ChatWindow isAdmin={false} />
    </div>
  );
}