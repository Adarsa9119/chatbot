import ChatWindow from '../components/ChatWindow';

export default function AdminChatPage() {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <ChatWindow isAdmin={true} />
    </div>
  );
}