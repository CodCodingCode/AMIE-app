
// Scene lighting
const BasicLights = () => (
    <>
      <ambientLight intensity={0.4} color="#b9d5ff" />
      <directionalLight position={[5, 8, 5]} intensity={1.2} color="#ffffff" castShadow shadow-mapSize={256} />
      <directionalLight position={[-5, 3, 0]} intensity={0.5} color="#4d71ff" />
    </>
  );

export default BasicLights;